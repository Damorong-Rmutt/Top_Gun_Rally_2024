import os
import asyncio
import mysql.connector
from fastapi import FastAPI, WebSocket, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse,StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import aiofiles
from datetime import datetime 
import paho.mqtt.client as mqtt
import zipfile
import time


app = FastAPI()
MQTT_BROKER = "mqtt-broker"  # Replace with Raspberry Pi IP or hostname
MQTT_PORT = 1883
MQTT_TOPIC_REQUEST_FILE = "raspberry/request_file"
# Configuration
UPLOAD_FOLDER = "uploads"
API_KEY = "e350e20f-7f1c-4dbb-be8f-54d4d154e45e"  # Replace with your actual API Key
ALLOWED_EXTENSIONS = {"wav", "mp3", "mp4","json","mlx"}
mqtt_client = mqtt.Client()
# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust domains for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def connect_mqtt():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print("Connected to MQTT Broker")
    except Exception as e:
        print(f"Failed to connect to MQTT Broker: {e}")

connect_mqtt()

# API: Command Raspberry Pi to Upload a File
@app.post("/raspberry/upload-file")
async def request_file_from_raspberry(file_name: str = Form(...), api_key: str = Form(...)):
    """
    ส่งคำสั่งให้ Raspberry Pi อัปโหลดไฟล์มายัง Server
    """
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    try:
        mqtt_client.publish(MQTT_TOPIC_REQUEST_FILE, file_name)
        return {"status": "success", "message": f"Requested file {file_name} from Raspberry Pi"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to request file: {e}"}
    
# Database Configuration
def init_mysql():
    try:
        conn = mysql.connector.connect(
            host="db",
            user="root",
            password="root",
            database="machine_data",
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        raise

# Function to check allowed file extensions
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# API: File Upload with Authentication
@app.post("/upload-audio")
async def upload_audio(
    audio: UploadFile = File(...),
    device_id: str = Form("unknown_device"),
    api_key: str = Form(...),
):
    # API Key Authentication
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    # Validate file type
    if not allowed_file(audio.filename):
        return JSONResponse({"error": "File type not allowed"}, status_code=400)

    filename = os.path.basename(audio.filename)
    file_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename))

    # Save file to disk
    try:
        with open(file_path, "wb") as f:
            while True:
                chunk = await audio.read(1024)  # Read file in chunks
                if not chunk:
                    break
                f.write(chunk)
        print(f"File saved to: {file_path}")

        # Additional: Save file to local backup folder
        local_backup_folder = "local_backup"
        if not os.path.exists(local_backup_folder):
            os.makedirs(local_backup_folder)
        backup_path = os.path.join(local_backup_folder, filename)
        with open(backup_path, "wb") as backup_file:
            with open(file_path, "rb") as original_file:
                backup_file.write(original_file.read())
        print(f"File backed up to: {backup_path}")

    except Exception as e:
        print(f"Error saving file: {e}")
        return JSONResponse({"error": f"Failed to save file: {e}"}, status_code=500)

    # Save or update file metadata in database
    try:
        conn = init_mysql()
        cursor = conn.cursor(dictionary=True)

        # Check if the file already exists in the database
        check_query = "SELECT file_id FROM audio_files WHERE file_name = %s"
        cursor.execute(check_query, (filename,))
        result = cursor.fetchone()

        if result:
            # Update existing record
            update_query = """
            UPDATE audio_files 
            SET file_path = %s, device_id = %s, upload_time = CURRENT_TIMESTAMP
            WHERE file_id = %s
            """
            cursor.execute(update_query, (file_path, device_id, result["file_id"]))
            print(f"File metadata updated for file: {filename}")
        else:
            # Insert new record
            insert_query = """
            INSERT INTO audio_files (file_name, file_path, device_id)
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (filename, file_path, device_id))
            print(f"File metadata inserted for file: {filename}")

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error while saving metadata: {e}")
        return JSONResponse({"error": f"Failed to save metadata: {str(e)}"}, status_code=500)

    return {
        "message": "File uploaded, backed up locally, and metadata saved successfully",
        "file_name": filename,
        "backup_path": backup_path
    }

@app.post("/upload-models")
async def upload_zip(
    zip_file: UploadFile = File(...),
    device_id: str = Form(...),
    api_key: str = Form(...)
):
    """
    Endpoint to upload a ZIP file containing machine learning models, extract them, and store metadata.
    """
    # Debug: Log received data
    print(f"Received API Key: {api_key}")
    print(f"Received Device ID: {device_id}")
    print(f"Received ZIP file: {zip_file.filename}")

    # API Key Authentication
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    # Save the ZIP file to disk
    zip_filename = os.path.basename(zip_file.filename)
    zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)

    try:
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        with open(zip_path, "wb") as f:
            while True:
                chunk = await zip_file.read(1024)
                if not chunk:
                    break
                f.write(chunk)
        print(f"ZIP file saved to: {zip_path}")

    except Exception as e:
        print(f"Error saving ZIP file: {e}")
        return JSONResponse({"error": f"Failed to save ZIP file: {e}"}, status_code=500)

    # Extract the ZIP file and save metadata for each file
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(path=UPLOAD_FOLDER)
            for filename in zip_ref.namelist():
                file_path = os.path.join(UPLOAD_FOLDER, filename)

                # Replace file if exists
                if os.path.exists(file_path):
                    os.remove(file_path)
                with open(file_path, "wb") as f:
                    f.write(zip_ref.read(filename))
                print(f"Extracted and replaced file: {filename}")

                # Save metadata for each file in the database
                conn = init_mysql()
                cursor = conn.cursor(dictionary=True)

                # Replace metadata in the database
                check_query = "SELECT model_id FROM models WHERE model_name = %s"
                cursor.execute(check_query, (filename,))
                result = cursor.fetchone()
                print(f"Check query result for {filename}: {result}")

                if result:
                    # Update existing record
                    update_query = """
                    UPDATE models 
                    SET model_path = %s, device_id = %s, upload_time = CURRENT_TIMESTAMP
                    WHERE model_id = %s
                    """
                    print(f"Updating metadata for model: {filename}")
                    cursor.execute(update_query, (file_path, device_id, result["model_id"]))
                else:
                    # Insert new record
                    insert_query = """
                    INSERT INTO models (model_name, model_path, device_id)
                    VALUES (%s, %s, %s)
                    """
                    print(f"Inserting metadata for model: {filename}")
                    cursor.execute(insert_query, (filename, file_path, device_id))

                conn.commit()
                cursor.close()
                conn.close()

    except Exception as e:
        print(f"Error extracting ZIP file or saving metadata: {e}")
        return JSONResponse({"error": f"Failed to process ZIP file: {e}"}, status_code=500)

    return {
        "message": "ZIP file uploaded, extracted, replaced, and metadata saved successfully"
    }


@app.get("/download-models/{tar_filename}")
async def download_models(tar_filename: str):
    tar_path = os.path.join(UPLOAD_FOLDER, tar_filename)

    if not os.path.exists(tar_path):
        raise HTTPException(status_code=404, detail="TAR file not found")

    return FileResponse(
        tar_path,
        media_type="application/x-tar",
        filename=tar_filename
    )

# API: Retrieve Uploaded Files
@app.get("/audio-files")
async def get_audio_files():
    try:
        conn = init_mysql()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT file_id, file_name, file_path, upload_time FROM audio_files")
        files = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"files": files}
    except Exception as e:
        return {"error": f"Failed to fetch files: {e}"}

@app.get("/models")
async def get_models():
    try:
        conn = init_mysql()  # ฟังก์ชันสำหรับเชื่อมต่อกับ MySQL
        cursor = conn.cursor(dictionary=True)
        # ดึงข้อมูลจากตาราง models
        cursor.execute("SELECT model_id, model_name, description, created_at FROM models")
        models = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"models": models}  # เปลี่ยนชื่อคีย์ให้สื่อถึงข้อมูลใหม่
    except Exception as e:
        return {"error": f"Failed to fetch models: {e}"}
    
# API: Download a Specific File
@app.get("/download-audio/{file_id}")
async def download_audio(file_id: int):
    try:
        conn = init_mysql()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT file_path FROM audio_files WHERE file_id = %s"
        cursor.execute(query, (file_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            file_path = result["file_path"]
            if os.path.exists(file_path):
                return FileResponse(file_path, media_type="audio/mpeg", filename=os.path.basename(file_path))
            else:
                raise HTTPException(status_code=404, detail="File not found")
        else:
            raise HTTPException(status_code=404, detail="File ID not found in database")
    except Exception as e:
        return {"error": f"Failed to process request: {e}"}

# API: Check File Upload Status
upload_status: Dict[str, str] = {}

@app.get("/upload-status/{file_name}")
async def get_upload_status(file_name: str):
    status = upload_status.get(file_name, "not_found")
    return {"file_name": file_name, "status": status}

# API: Sensor Data Retrieval (Example for DB Integration)
@app.get("/sensor")
async def get_sensor_data():
    try:
        conn = init_mysql()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM sensor_data"
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"status": "success", "sensor_data": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# WebSocket: Real-Time Audio File Updates
@app.websocket("/ws")
async def websocket_audio_files(websocket: WebSocket):
    await websocket.accept()
    try:
        conn = init_mysql()
        cursor = conn.cursor(dictionary=True)
        while True:
            cursor.execute("SELECT file_id, file_name, file_path, upload_time FROM audio_files")
            results = cursor.fetchall()
            await websocket.send_json({"status": "success", "audio_files": results})
            await asyncio.sleep(5)  # Send updates every 5 seconds
    except Exception as e:
        print(f"WebSocket Error: {e}")
        await websocket.close()
    finally:
        cursor.close()
        conn.close()

@app.delete("/delete-audio/{file_id}")
async def delete_audio(file_id: int):
    try:
        # ค้นหาไฟล์ในฐานข้อมูล
        conn = init_mysql()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT file_path FROM audio_files WHERE file_id = %s"
        cursor.execute(query, (file_id,))
        result = cursor.fetchone()

        if result:
            file_path = result["file_path"]
            
            # ลบไฟล์จากระบบไฟล์
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File deleted from disk: {file_path}")
            else:
                print(f"File not found on disk: {file_path}")

            # ลบข้อมูลในฐานข้อมูล
            delete_query = "DELETE FROM audio_files WHERE file_id = %s"
            cursor.execute(delete_query, (file_id,))
            conn.commit()
            cursor.close()
            conn.close()

            return {"message": "File and database entry deleted successfully", "file_id": file_id}
        else:
            raise HTTPException(status_code=404, detail="File ID not found in database")
    except Exception as e:
        return {"error": f"Failed to delete file: {e}"}
    
@app.get("/play-audio/{file_id}")
async def play_audio(file_id: int):
    try:
        # ค้นหาไฟล์ในฐานข้อมูล
        conn = init_mysql()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT file_path FROM audio_files WHERE file_id = %s"
        cursor.execute(query, (file_id,))
        result = cursor.fetchone()

        if result:
            file_path = result["file_path"]
            if os.path.exists(file_path):
                # สตรีมไฟล์ WAV
                async def file_streamer():
                    async with aiofiles.open(file_path, mode="rb") as file:
                        while chunk := await file.read(1024):
                            yield chunk

                return StreamingResponse(file_streamer(), media_type="audio/wav")
            else:
                raise HTTPException(status_code=404, detail="File not found on disk")
        else:
            raise HTTPException(status_code=404, detail="File ID not found in database")
    except Exception as e:
        print(f"Error while streaming audio: {e}")
        return {"error": f"Failed to play audio: {e}"}
    
@app.get("/sensor-by-date")
async def get_sensor_data_by_date(start_date: str, end_date: str):
    """
    ดึงข้อมูลจากตาราง sensor_data ตามช่วงวันที่ที่ระบุ
    :param start_date: วันที่เริ่มต้นในรูปแบบ YYYY-MM-DD
    :param end_date: วันที่สิ้นสุดในรูปแบบ YYYY-MM-DD
    """
    try:
        # ตรวจสอบรูปแบบวันที่
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # เชื่อมต่อกับฐานข้อมูล
        conn = init_mysql()
        cursor = conn.cursor(dictionary=True)
        
        # คำสั่ง SQL สำหรับดึงข้อมูลตามช่วงวันที่
        query = """
        SELECT * FROM sensor_data
        WHERE DATE(timestamp) BETWEEN %s AND %s
        """
        cursor.execute(query, (start_date, end_date))
        results = cursor.fetchall()
        
        # ปิดการเชื่อมต่อฐานข้อมูล
        cursor.close()
        conn.close()
        
        return {"status": "success", "sensor_data": results}
    except mysql.connector.Error as e:
        return {"status": "error", "message": f"Database error: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
