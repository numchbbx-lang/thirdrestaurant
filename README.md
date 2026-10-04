# thirdrestaurant

ระบบจัดการร้านอาหารแบบ SPA สำหรับ Admin, Staff และ Customer

## สถาปัตยกรรม

- Frontend: HTML / CSS / Vanilla JavaScript
- Backend: Python Standard Library บน Vercel Python Runtime
- Authentication: Firebase Authentication REST API
- Database: Upstash Redis REST API
- Hosting: Vercel
- Password reset: Firebase ส่งอีเมล Reset Password

> Repository นี้เป็น Public ได้ แต่ **ห้าม Commit API Key ที่เป็นความลับ, Upstash Token, Bootstrap Secret หรือ Password จริง**

## Environment Variables บน Vercel

ตั้งค่าใน Project Settings → Environment Variables:

```text
FIREBASE_API_KEY=...
UPSTASH_REDIS_REST_URL=https://....upstash.io
UPSTASH_REDIS_REST_TOKEN=...
UPSTASH_KEY_PREFIX=thirdrestaurant
BOOTSTRAP_SECRET=สุ่มค่าอย่างน้อย 32 ตัว
LOCAL_AUTH_SECRET=สุ่มค่าอย่างน้อย 32 ตัว
```

ตั้งค่าอย่างน้อยใน Environment `Production` และ Redeploy หลังแก้ไขค่า

## Firebase Authentication

ใน Firebase Console ให้เปิด:

```text
Authentication → Sign-in method → Email/Password → Enable
```

Firebase ใช้สำหรับ Login, Register และส่งลิงก์ Forgot Password ส่วนข้อมูลร้านอาหารและ Profile อยู่ใน Upstash Redis

## Upstash Redis

สร้าง Redis Database ใน Upstash Console แล้วคัดลอกค่า:

- HTTPS REST URL → `UPSTASH_REDIS_REST_URL`
- Token → `UPSTASH_REDIS_REST_TOKEN`

ระบบจัดเก็บข้อมูลแต่ละ Collection เป็น JSON ใน Redis key ที่มี Prefix เช่น:

```text
thirdrestaurant:users
thirdrestaurant:menus
thirdrestaurant:orders
```

## สร้าง Admin ครั้งแรก

หลัง Deploy ให้เรียก API นี้ครั้งเดียว:

```bash
curl -X POST https://YOUR-DOMAIN.vercel.app/api/bootstrap \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "ค่าเดียวกับ BOOTSTRAP_SECRET",
    "email": "admin-new@example.com",
    "password": "ใส่รหัสผ่านชุดใหม่ที่ปลอดภัย",
    "name": "Restaurant Admin"
  }'
```

จากนั้น Login เป็น Admin และใช้เมนู Staff / Users เพื่อสร้างบัญชี Staff ชุดใหม่

หลัง Bootstrap สำเร็จ ควรเปลี่ยนหรือลบ `BOOTSTRAP_SECRET` แล้ว Redeploy

## Forgot Password

หน้า Login มีปุ่ม `ลืมรหัสผ่าน?` ระบบจะส่งคำขอไปที่ Firebase Authentication และตอบข้อความกลางเพื่อไม่เปิดเผยว่าอีเมลมีบัญชีหรือไม่

## Deploy

เชื่อม Repository กับ Vercel หรือใช้ CLI:

```bash
vercel --prod
```

ตรวจระบบหลัง Deploy:

```text
https://YOUR-DOMAIN.vercel.app/api/health
```

ควรได้ `database_configured: true`

## Local Development

หากไม่มี Firebase และ Upstash ระบบจะใช้ Local fallback ที่ `data/database.json`:

```bash
python api/index.py
```

เปิด:

```text
http://127.0.0.1:8000/
```

## Roles

- Admin: Dashboard, Menu, Users/Staff, Audit Logs
- Staff: Tables, POS, Kitchen, Reservations, Checkout
- Customer: Reservation, QR Menu, Cart, Order Tracking, Member Points
