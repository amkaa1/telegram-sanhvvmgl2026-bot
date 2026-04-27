# Security Policy

## Sensitive Credentials

- `BOT_TOKEN`, `DATABASE_URL`, `ADMIN_IDS`, `GROUP_ID` зэрэг бүх нууц утгыг зөвхөн Railway Variables эсвэл локал `.env` дотор хадгална.
- Код, commit message, screenshot, log файлд нууц утга оруулахгүй.
- Хэрэв нууц утга репод орсон бол тэр даруй rotate хийнэ.

## Required Manual Action

- Энэ төслийн өмнөх хувилбарт Railway PostgreSQL connection string ил гарсан тул Railway дээр PostgreSQL password-аа заавал rotate хийнэ үү.
- Rotate хийсний дараа Railway `DATABASE_URL` болон локал `.env` утгаа шинэчилж deploy хийнэ.

## Reporting

Эмзэг байдал илэрвэл repo owner-т шууд private байдлаар мэдээлнэ үү.
