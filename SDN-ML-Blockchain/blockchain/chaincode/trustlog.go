/*
 * SPDX-License-Identifier: Apache-2.0
 *
 * SDN Security Event Logger - Chaincode for Hyperledger Fabric
 * Records security events from SDN controller including attacks, mitigations, and trust scores
 */

package main

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SecurityEvent represents a security event in the SDN network
type SecurityEvent struct {
	EventID      string                 `json:"event_id"`
	EventType    string                 `json:"event_type"` // attack_detected, port_blocked, switch_connected, etc.
	SwitchID     string                 `json:"switch_id"`
	Timestamp    int64                  `json:"timestamp"`
	TrustScore   float64                `json:"trust_score"` // 0.0 to 1.0
	Action       string                 `json:"action"`
	Details      map[string]interface{} `json:"details"`
	RecordedBy   string                 `json:"recorded_by"` // Controller ID
	RecordedTime int64                  `json:"recorded_time"`
}

// TrustLog represents trust information for a device
type TrustLog struct {
	DeviceID     string  `json:"device_id"`
	CurrentTrust float64 `json:"current_trust"`
	EventCount   int     `json:"event_count"`
	LastUpdate   int64   `json:"last_update"`
	Status       string  `json:"status"` // trusted, suspicious, blocked
}

// SmartContract provides functions for managing security events
type SmartContract struct {
	contractapi.Contract
}

// InitLedger initializes the ledger with sample data
func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	fmt.Println("Initializing SDN Security Ledger...")
	return nil
}

// RecordEvent records a new security event
func (s *SmartContract) RecordEvent(ctx contractapi.TransactionContextInterface, eventJSON string) error {
	var event SecurityEvent
	err := json.Unmarshal([]byte(eventJSON), &event)
	if err != nil {
		return fmt.Errorf("failed to unmarshal event: %v", err)
	}

	// Generate event ID if not provided. Use the transaction ID so it's deterministic across endorsers.
	if event.EventID == "" {
		txid := ctx.GetStub().GetTxID()
		event.EventID = fmt.Sprintf("EVT-%s-%s", event.SwitchID, txid)
	}

	// If the client provided a recorded_time use it so endorsers remain deterministic.
	// Otherwise use the transaction timestamp (deterministic) and only fallback to local time if unavailable.
	if event.RecordedTime == 0 {
		if ts, err := ctx.GetStub().GetTxTimestamp(); err == nil && ts != nil {
			event.RecordedTime = ts.Seconds
		} else {
			event.RecordedTime = time.Now().Unix()
		}
	}

	// Get client identity
	clientID, err := ctx.GetClientIdentity().GetID()
	if err != nil {
		return fmt.Errorf("failed to get client identity: %v", err)
	}
	event.RecordedBy = clientID

	eventBytes, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to marshal event: %v", err)
	}

	// Store event in ledger
	err = ctx.GetStub().PutState(event.EventID, eventBytes)
	if err != nil {
		return fmt.Errorf("failed to put event to ledger: %v", err)
	}

	// Update device trust log
	// Pass RecordedTime so endorsers use the same timestamp when updating the trust log
	err = s.updateTrustLog(ctx, event.SwitchID, event.TrustScore, event.EventType, event.RecordedTime)
	if err != nil {
		return fmt.Errorf("failed to update trust log: %v", err)
	}

	fmt.Printf("Event recorded: %s - %s\n", event.EventID, event.EventType)
	return nil
}

// updateTrustLog updates or creates trust log for a device
func (s *SmartContract) updateTrustLog(ctx contractapi.TransactionContextInterface, deviceID string, trustScore float64, eventType string, lastUpdate int64) error {
	trustKey := "TRUST-" + deviceID
	trustBytes, err := ctx.GetStub().GetState(trustKey)

	var trustLog TrustLog

	if err == nil && trustBytes != nil {
		// Update existing trust log
		err = json.Unmarshal(trustBytes, &trustLog)
		if err != nil {
			return fmt.Errorf("failed to unmarshal trust log: %v", err)
		}

		// Update trust score (weighted average)
		trustLog.CurrentTrust = (trustLog.CurrentTrust*float64(trustLog.EventCount) + trustScore) / float64(trustLog.EventCount+1)
		trustLog.EventCount++
	} else {
		// Create new trust log
		trustLog = TrustLog{
			DeviceID:     deviceID,
			CurrentTrust: trustScore,
			EventCount:   1,
			Status:       "trusted",
		}
	}

	// Use the provided lastUpdate (from the recorded event) so endorsers produce deterministic write sets
	trustLog.LastUpdate = lastUpdate

	// Update status based on trust score
	if trustLog.CurrentTrust < 0.3 {
		trustLog.Status = "blocked"
	} else if trustLog.CurrentTrust < 0.6 {
		trustLog.Status = "suspicious"
	} else {
		trustLog.Status = "trusted"
	}

	trustBytes, err = json.Marshal(trustLog)
	if err != nil {
		return fmt.Errorf("failed to marshal trust log: %v", err)
	}

	return ctx.GetStub().PutState(trustKey, trustBytes)
}

// QueryEvent retrieves a specific event
func (s *SmartContract) QueryEvent(ctx contractapi.TransactionContextInterface, eventID string) (*SecurityEvent, error) {
	eventBytes, err := ctx.GetStub().GetState(eventID)
	if err != nil {
		return nil, fmt.Errorf("failed to read from ledger: %v", err)
	}
	if eventBytes == nil {
		return nil, fmt.Errorf("event %s does not exist", eventID)
	}

	var event SecurityEvent
	err = json.Unmarshal(eventBytes, &event)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal event: %v", err)
	}

	return &event, nil
}

// QueryTrustLog retrieves trust information for a device
func (s *SmartContract) QueryTrustLog(ctx contractapi.TransactionContextInterface, deviceID string) (*TrustLog, error) {
	trustKey := "TRUST-" + deviceID
	trustBytes, err := ctx.GetStub().GetState(trustKey)
	if err != nil {
		return nil, fmt.Errorf("failed to read trust log: %v", err)
	}
	if trustBytes == nil {
		return nil, fmt.Errorf("trust log for device %s does not exist", deviceID)
	}

	var trustLog TrustLog
	err = json.Unmarshal(trustBytes, &trustLog)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal trust log: %v", err)
	}

	return &trustLog, nil
}

// QueryEventsBySwitch retrieves all events for a specific switch
func (s *SmartContract) QueryEventsBySwitch(ctx contractapi.TransactionContextInterface, switchID string) ([]*SecurityEvent, error) {
	queryString := fmt.Sprintf(`{"selector":{"switch_id":"%s"}}`, switchID)
	return s.queryEvents(ctx, queryString)
}

// QueryEventsByType retrieves all events of a specific type
func (s *SmartContract) QueryEventsByType(ctx contractapi.TransactionContextInterface, eventType string) ([]*SecurityEvent, error) {
	queryString := fmt.Sprintf(`{"selector":{"event_type":"%s"}}`, eventType)
	return s.queryEvents(ctx, queryString)
}

// QueryEventsByTimeRange retrieves events within a time range
func (s *SmartContract) QueryEventsByTimeRange(ctx contractapi.TransactionContextInterface, startTime, endTime int64) ([]*SecurityEvent, error) {
	queryString := fmt.Sprintf(`{"selector":{"timestamp":{"$gte":%d,"$lte":%d}}}`, startTime, endTime)
	return s.queryEvents(ctx, queryString)
}

// queryEvents is a helper function for rich queries
func (s *SmartContract) queryEvents(ctx contractapi.TransactionContextInterface, queryString string) ([]*SecurityEvent, error) {
	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, fmt.Errorf("failed to execute query: %v", err)
	}
	defer resultsIterator.Close()

	var events []*SecurityEvent
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, fmt.Errorf("failed to iterate results: %v", err)
		}

		var event SecurityEvent
		err = json.Unmarshal(queryResponse.Value, &event)
		if err != nil {
			return nil, fmt.Errorf("failed to unmarshal event: %v", err)
		}
		events = append(events, &event)
	}

	return events, nil
}

// GetAllEvents retrieves all security events (for testing, use with caution in production)
func (s *SmartContract) GetAllEvents(ctx contractapi.TransactionContextInterface) ([]*SecurityEvent, error) {
	resultsIterator, err := ctx.GetStub().GetStateByRange("EVT-", "EVT-~")
	if err != nil {
		return nil, fmt.Errorf("failed to get all events: %v", err)
	}
	defer resultsIterator.Close()

	var events []*SecurityEvent
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, fmt.Errorf("failed to iterate results: %v", err)
		}

		var event SecurityEvent
		err = json.Unmarshal(queryResponse.Value, &event)
		if err != nil {
			continue // Skip invalid entries
		}
		if event.Details == nil {
			event.Details = make(map[string]interface{})
		}
		events = append(events, &event)
	}

	return events, nil
}

// GetRecentAttacks retrieves recent attack events across all switches within timeWindow seconds
func (s *SmartContract) GetRecentAttacks(ctx contractapi.TransactionContextInterface, timeWindow int64) ([]*SecurityEvent, error) {
	currentTime := time.Now().Unix()
	startTime := currentTime - timeWindow

	// Use range query instead of rich query for LevelDB compatibility
	resultsIterator, err := ctx.GetStub().GetStateByRange("EVT-", "EVT-~")
	if err != nil {
		return nil, fmt.Errorf("failed to get events: %v", err)
	}
	defer resultsIterator.Close()

	var attacks []*SecurityEvent
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, fmt.Errorf("failed to iterate results: %v", err)
		}

		var event SecurityEvent
		err = json.Unmarshal(queryResponse.Value, &event)
		if err != nil {
			continue // Skip invalid entries
		}

		// Filter by event type and time
		if event.EventType == "attack_detected" && event.Timestamp >= startTime {
			if event.Details == nil {
				event.Details = make(map[string]interface{})
			}
			attacks = append(attacks, &event)
		}
	}

	return attacks, nil
}

// GetMitigationAction determines the appropriate mitigation action based on trust score and history
func (s *SmartContract) GetMitigationAction(ctx contractapi.TransactionContextInterface, switchID string, confidence float64) (string, error) {
	trustLog, err := s.QueryTrustLog(ctx, switchID)
	if err != nil {
		// No trust log exists, use default behavior
		if confidence > 0.9 {
			return "standard_mitigation", nil
		}
		return "warn_only", nil
	}

	// High confidence attack
	if confidence > 0.95 {
		return "block_immediately", nil
	}

	// Medium confidence - check trust history
	if confidence > 0.7 {
		if trustLog.CurrentTrust < 0.5 {
			// Low trust + medium confidence = block
			return "block_immediately", nil
		} else if trustLog.CurrentTrust > 0.8 {
			// High trust + medium confidence = warn only
			return "warn_only", nil
		}
		return "standard_mitigation", nil
	}

	// Low confidence - only block if very low trust
	if trustLog.CurrentTrust < 0.3 {
		return "standard_mitigation", nil
	}

	return "warn_only", nil
}

// CoordinatedAttackResult represents the result of coordinated attack check
type CoordinatedAttackResult struct {
	IsCoordinated    bool     `json:"is_coordinated"`
	AffectedSwitches []string `json:"affected_switches"`
	AttackCount      int      `json:"attack_count"`
}

// CheckCoordinatedAttack checks if multiple switches are under attack (coordinated DDoS)
func (s *SmartContract) CheckCoordinatedAttack(ctx contractapi.TransactionContextInterface, timeWindow int64, threshold int) (string, error) {
	attacks, err := s.GetRecentAttacks(ctx, timeWindow)
	if err != nil {
		return "", fmt.Errorf("failed to get recent attacks: %v", err)
	}

	// Count unique switches under attack
	switchMap := make(map[string]bool)
	for _, attack := range attacks {
		switchMap[attack.SwitchID] = true
	}

	affectedSwitches := make([]string, 0, len(switchMap))
	for switchID := range switchMap {
		affectedSwitches = append(affectedSwitches, switchID)
	}

	isCoordinated := len(affectedSwitches) >= threshold

	result := CoordinatedAttackResult{
		IsCoordinated:    isCoordinated,
		AffectedSwitches: affectedSwitches,
		AttackCount:      len(attacks),
	}

	resultJSON, err := json.Marshal(result)
	if err != nil {
		return "", fmt.Errorf("failed to marshal result: %v", err)
	}

	return string(resultJSON), nil
}

// MitigationPolicy represents a mitigation policy stored on blockchain
type MitigationPolicy struct {
	PolicyID      string  `json:"policy_id"`
	Name          string  `json:"name"`
	MinConfidence float64 `json:"min_confidence"`
	MinTrustScore float64 `json:"min_trust_score"`
	Action        string  `json:"action"`         // block_immediately, standard_mitigation, warn_only
	BlockDuration int     `json:"block_duration"` // seconds
	Description   string  `json:"description"`
	CreatedBy     string  `json:"created_by"`
	CreatedTime   int64   `json:"created_time"`
}

// SetMitigationPolicy creates or updates a mitigation policy
func (s *SmartContract) SetMitigationPolicy(ctx contractapi.TransactionContextInterface, policyJSON string) error {
	var policy MitigationPolicy
	err := json.Unmarshal([]byte(policyJSON), &policy)
	if err != nil {
		return fmt.Errorf("failed to unmarshal policy: %v", err)
	}

	if policy.PolicyID == "" {
		return fmt.Errorf("policy_id is required")
	}

	// Get client identity
	clientID, err := ctx.GetClientIdentity().GetID()
	if err != nil {
		return fmt.Errorf("failed to get client identity: %v", err)
	}
	policy.CreatedBy = clientID
	policy.CreatedTime = time.Now().Unix()

	policyBytes, err := json.Marshal(policy)
	if err != nil {
		return fmt.Errorf("failed to marshal policy: %v", err)
	}

	policyKey := "POLICY-" + policy.PolicyID
	err = ctx.GetStub().PutState(policyKey, policyBytes)
	if err != nil {
		return fmt.Errorf("failed to put policy to ledger: %v", err)
	}

	fmt.Printf("Policy set: %s - %s\n", policy.PolicyID, policy.Name)
	return nil
}

// GetMitigationPolicy retrieves a mitigation policy
func (s *SmartContract) GetMitigationPolicy(ctx contractapi.TransactionContextInterface, policyID string) (*MitigationPolicy, error) {
	policyKey := "POLICY-" + policyID
	policyBytes, err := ctx.GetStub().GetState(policyKey)
	if err != nil {
		return nil, fmt.Errorf("failed to read policy: %v", err)
	}
	if policyBytes == nil {
		return nil, fmt.Errorf("policy %s does not exist", policyID)
	}

	var policy MitigationPolicy
	err = json.Unmarshal(policyBytes, &policy)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal policy: %v", err)
	}

	return &policy, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		fmt.Printf("Error creating SDN security chaincode: %v\n", err)
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting SDN security chaincode: %v\n", err)
	}
}
