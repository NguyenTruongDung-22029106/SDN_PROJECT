# Hướng Dẫn Push Code Lên GitHub

## Thông Tin Repo

- **Repository URL**: https://github.com/NguyenTruongDung-22029106/SDN-PROJECT-SEC.git
- **Branch hiện tại**: `feature/fabric-client-ctor`
- **Remote name**: `origin`

---

## Các Bước Push Code

### Bước 1: Kiểm tra trạng thái hiện tại

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain

# Xem trạng thái git
git status

# Xem remote đã được set chưa
git remote -v

# Xem branch hiện tại
git branch
```

### Bước 2: Kiểm tra và cập nhật remote (nếu cần)

```bash
# Kiểm tra remote
git remote -v

# Nếu chưa có remote hoặc sai URL, thêm/sửa:
git remote set-url origin https://github.com/NguyenTruongDung-22029106/SDN-PROJECT-SEC.git

# Hoặc nếu chưa có remote:
git remote add origin https://github.com/NguyenTruongDung-22029106/SDN-PROJECT-SEC.git
```

### Bước 3: Thêm các file đã thay đổi

```bash
# Xem các file đã thay đổi
git status

# Thêm tất cả file đã thay đổi
git add .

# Hoặc thêm từng file cụ thể
git add README.md
git add docs/
git add blockchain/
# ...
```

**Lưu ý:** File sẽ được filter theo `.gitignore`:
- Sẽ commit: source code, docs, scripts, configs
- Sẽ bỏ qua: `fabric-samples/`, `node_modules/`, `*.log`, `*.pkl`, `wallet/`, `venv/`

### Bước 4: Commit các thay đổi

```bash
# Commit với message mô tả
git commit -m "feat: Update SDN-ML-Blockchain project

- Update gateway_node_server.js with auto-generated connection profile
- Add comprehensive documentation (HUONG_DAN_XEM_BLOCKCHAIN.md)
- Update MANUAL_SETUP.md with troubleshooting guides
- Remove redundant files and scripts
- Fix port configuration (3000 -> 3001)
- Improve blockchain integration and error handling"

# Hoặc commit ngắn gọn
git commit -m "Update project: improve blockchain integration and documentation"
```

### Bước 5: Push lên GitHub

```bash
# Push lên branch hiện tại (feature/fabric-client-ctor)
git push origin feature/fabric-client-ctor

# Hoặc nếu muốn push lên main/master
git push origin feature/fabric-client-ctor:main

# Nếu lần đầu push branch mới
git push -u origin feature/fabric-client-ctor
```

---

## Workflow Thông Thường

### Làm việc với branch hiện tại

```bash
# 1. Kiểm tra status
git status

# 2. Thêm changes
git add .

# 3. Commit
git commit -m "Your commit message"

# 4. Push
git push origin feature/fabric-client-ctor
```

### Tạo branch mới (nếu cần)

```bash
# Tạo và chuyển sang branch mới
git checkout -b feature/new-feature

# Hoặc
git branch feature/new-feature
git checkout feature/new-feature

# Push branch mới lên GitHub
git push -u origin feature/new-feature
```

### Merge vào main/master

```bash
# Chuyển sang main
git checkout main

# Pull code mới nhất
git pull origin main

# Merge branch feature vào main
git merge feature/fabric-client-ctor

# Push lên GitHub
git push origin main
```

---

## Xử Lý Lỗi Thường Gặp

### Lỗi 1: "Updates were rejected"

**Nguyên nhân:** Remote có code mới hơn local

**Giải pháp:**
```bash
# Pull code từ remote trước
git pull origin feature/fabric-client-ctor --rebase

# Hoặc merge
git pull origin feature/fabric-client-ctor

# Sau đó push lại
git push origin feature/fabric-client-ctor
```

### Lỗi 2: "Authentication failed"

**Nguyên nhân:** Chưa đăng nhập hoặc token hết hạn

**Giải pháp:**
```bash
# Dùng Personal Access Token thay vì password
# Tạo token tại: GitHub Settings > Developer settings > Personal access tokens

# Hoặc setup SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"
# Copy public key vào GitHub Settings > SSH Keys
```

### Lỗi 3: "Large files detected"

**Nguyên nhân:** Có file quá lớn (>100MB)

**Giải pháp:**
```bash
# Kiểm tra file lớn
git ls-files | xargs du -h | sort -rh | head -20

# Thêm vào .gitignore nếu không cần thiết
echo "large_file.pkl" >> .gitignore

# Xóa khỏi git cache
git rm --cached large_file.pkl
git commit -m "Remove large files"
git push origin feature/fabric-client-ctor
```

### Lỗi 4: "Branch not found"

**Nguyên nhân:** Branch chưa tồn tại trên remote

**Giải pháp:**
```bash
# Push với -u để set upstream
git push -u origin feature/fabric-client-ctor
```

---

## Checklist Trước Khi Push

- [ ] Đã kiểm tra `git status` - không có file nhạy cảm (passwords, keys)
- [ ] Đã test code - không có lỗi nghiêm trọng
- [ ] Đã commit message rõ ràng - mô tả được thay đổi
- [ ] Đã kiểm tra `.gitignore` - file không cần thiết đã được ignore
- [ ] Đã pull code mới nhất - tránh conflict
- [ ] Đã backup code quan trọng - phòng trường hợp cần rollback

---

## Quick Commands

### Push nhanh (sau khi đã setup)

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain
git add .
git commit -m "Update: [mô tả ngắn gọn]"
git push origin feature/fabric-client-ctor
```

### Xem lịch sử commit

```bash
# Xem commit history
git log --oneline -10

# Xem thay đổi của commit cụ thể
git show <commit-hash>

# Xem diff trước khi commit
git diff
```

### Undo changes (nếu cần)

```bash
# Undo file chưa add
git restore <file>

# Undo tất cả changes chưa commit
git restore .

# Undo commit (giữ changes)
git reset --soft HEAD~1

# Undo commit (xóa changes)
git reset --hard HEAD~1
```

---

## Tài Liệu Tham Khảo

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Docs](https://docs.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

---

## Tips

1. **Commit thường xuyên**: Commit từng feature nhỏ thay vì commit một lần lớn
2. **Message rõ ràng**: Viết commit message mô tả rõ thay đổi
3. **Pull trước push**: Luôn pull trước khi push để tránh conflict
4. **Review code**: Xem lại `git diff` trước khi commit
5. **Backup**: Luôn backup code quan trọng trước khi push

---

## Liên Kết Hữu Ích

- **Repo trên GitHub**: https://github.com/NguyenTruongDung-22029106/SDN-PROJECT-SEC
- **GitHub Desktop** (GUI tool): https://desktop.github.com/
- **GitKraken** (GUI tool): https://www.gitkraken.com/

---

**Lưu ý:** Nếu gặp vấn đề, kiểm tra lại:
1. Internet connection
2. GitHub authentication
3. Branch permissions
4. File size limits

