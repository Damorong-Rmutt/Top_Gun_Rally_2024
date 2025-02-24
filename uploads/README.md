
## อธิบาย ไฟล์ทั้งหมด

# - โฟลเดอร์ db_jwt
    - ประกอบไปด้วย
        - statics
            - style
                - style.css # ไฟล์ css ของ Index
                - output.css # ไฟล์ css ของ Index ที่สร้างโดย Tailwind
         - Template
            - Index.html #ไฟล์แสดงผลลัพธ์ของ Database
            - Login.html #ใช้สำหรับเข้าสู่ระบบเพื่อแสดงผลลัพธ์
        - app.py #ใช้สำหรับกำหนด API เพื่อใช้ร่วมกับ Database
        - fetch.py #ใช้สำหรับ Insert ข้อมูลจาก Websocket เข้าสู่ Database
        - package.json , package-lock.json - Tailwind.config.js #ไฟล์ ของ Tailwind CSS
-----
# - โฟลเดอร์ fetch_ws
    - ประกอบไปด้วย
        - css
            - style.css # ไฟล์ css ของ Index
            - output.css # ไฟล์ css ของ Index ที่สร้างโดย 
        - index.html #ใช้ดึง Websocket มาแสดงในรูปแบบของ Charts ต่าง ๆ

