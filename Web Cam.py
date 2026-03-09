from flask import Flask, request, send_from_directory, render_template_string, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

# ------------------------- Helpers -------------------------
def is_allowed(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXT

# ------------------------- Upload API -------------------------
@app.route("/upload", methods=["POST"])
def upload():
    if "imageFile" not in request.files:
        return jsonify({"ok": False, "msg": "No file field named imageFile"}), 400

    file = request.files["imageFile"]
    if not file or file.filename.strip() == "":
        return jsonify({"ok": False, "msg": "Empty filename"}), 400

    if not is_allowed(file.filename):
        return jsonify({"ok": False, "msg": "Only images are allowed"}), 400

    # اسم ملف آمن + طابع زمني لضمان التفرد
    safe_name = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")
    filename = f"{timestamp}_{safe_name}"

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return jsonify({"ok": True, "filename": filename}), 200

# ------------------------- Serve files -------------------------
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)

# ------------------------- List API -------------------------
@app.route("/api/images")
def api_images():
    images = [
        f for f in os.listdir(UPLOAD_FOLDER)
        if os.path.splitext(f)[1].lower() in ALLOWED_EXT
    ]
    images.sort(reverse=True)  # الأحدث أولاً
    return jsonify(images)

# ------------------------- UI -------------------------
@app.route("/")
def gallery():
    html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Website Cam — Live Image Gallery</title>

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"/>

  <style>
    :root{
      --bg:#0f1115; --card:#151922; --text:#e9eef7; --muted:#a7b0c3;
      --accent:#00e0c6; --accent-2:#7cf7e8; --danger:#ff5d5d;
    }
    *{box-sizing:border-box}
    body{
      margin:0; background:linear-gradient(180deg, #0b0e13 0%, #121725 100%); 
      color:var(--text); font-family:'Cairo', system-ui, -apple-system, Segoe UI, Arial, sans-serif;
    }
    header{
      padding:24px 16px; text-align:center; position:sticky; top:0; z-index:5;
      backdrop-filter:saturate(160%) blur(6px);
      background:rgba(15,17,21,0.6); border-bottom:1px solid rgba(255,255,255,0.06);
    }
    header h1{margin:0;font-size:28px;letter-spacing:.3px}
    header p{margin:6px 0 0;color:var(--muted);font-size:14px}

    .container{max-width:1100px;margin:18px auto;padding:0 16px}

    /* Uploader card */
    .uploader{
      background:var(--card); border:1px solid rgba(255,255,255,0.06);
      border-radius:14px; padding:18px; display:grid; gap:14px;
    }
    .row{display:flex; gap:10px; align-items:center; flex-wrap:wrap}
    input[type=file]{display:none}
    .btn{
      background:var(--accent); color:#0b0e13; border:none; padding:10px 16px;
      border-radius:10px; cursor:pointer; font-weight:700; transition:transform .08s ease;
    }
    .btn:hover{transform:translateY(-1px)}
    .muted{color:var(--muted); font-size:13px}

    .dropzone{
      width:100%; border:2px dashed rgba(255,255,255,0.2);
      border-radius:12px; padding:18px; text-align:center; color:var(--muted);
      transition:border-color .2s, background .2s;
    }
    .dropzone.dragover{border-color:var(--accent); background:rgba(0,224,198,0.05)}

    /* Progress */
    .progress-wrap{width:100%; background:#1a2130; border-radius:10px; overflow:hidden; height:10px; display:none}
    .progress{height:100%; width:0%; background:linear-gradient(90deg, var(--accent), var(--accent-2));}

    /* Gallery grid */
    .grid{
      margin-top:18px; display:grid;
      grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:10px;
    }
    .card{
      background:#0f141d; border:1px solid rgba(255,255,255,0.06); border-radius:12px;
      overflow:hidden; position:relative; cursor:pointer;
      transition:transform .15s ease, box-shadow .15s ease;
    }
    .card:hover{transform:translateY(-2px); box-shadow:0 6px 26px rgba(0,0,0,0.35)}
    .thumb{width:100%; height:150px; object-fit:cover; display:block}
    .badge{
      position:absolute; left:10px; top:10px; font-size:11px; padding:5px 8px;
      background:rgba(0,0,0,0.55); border:1px solid rgba(255,255,255,0.12); color:#fff; border-radius:8px;
    }

    /* Lightbox */
    .lightbox{position:fixed; inset:0; background:rgba(0,0,0,.85); display:none; align-items:center; justify-content:center; z-index:20}
    .lightbox.open{display:flex}
    .lightbox img{max-width:92vw; max-height:88vh; border-radius:12px; border:2px solid rgba(255,255,255,0.12)}
    .close{
      position:fixed; top:14px; right:14px; background:transparent; color:#fff;
      border:1px solid rgba(255,255,255,0.25); border-radius:10px; padding:6px 10px; cursor:pointer
    }

    footer{color:#7f8aa4; text-align:center; font-size:12px; padding:18px 0 28px}
  </style>
</head>
<body>
  <header>
    <h1>Website Cam — Live Image Gallery</h1>
    <p>ارفع صور الـ ESP32‑CAM وشوفيها فورًا في الجاليري.</p>
  </header>

  <div class="container">

    <div class="uploader" id="uploader">
      <div class="row">
        <label for="file" class="btn">اختاري صورة</label>
        <input id="file" type="file" accept="image/*" />
        <button id="btnUpload" class="btn" style="background:#8fff73">رفع</button>
        <span class="muted">أو اسحبي الصورة داخل المربع…</span>
      </div>

      <div id="dz" class="dropzone">Drop files here</div>

      <div class="progress-wrap" id="pgWrap"><div class="progress" id="pg"></div></div>
      <div id="msg" class="muted"></div>
    </div>

    <div class="grid" id="gallery"></div>

  </div>

  <!-- Lightbox -->
  <div class="lightbox" id="lb" role="dialog" aria-modal="true">
    <button class="close" id="lbClose">إغلاق ✕</button>
    <img id="lbImg" alt="preview"/>
  </div>

  <footer>© {{year}} Website Cam</footer>

  <script>
    const gallery = document.getElementById("gallery");
    const fileInput = document.getElementById("file");
    const btnUpload = document.getElementById("btnUpload");
    const dz = document.getElementById("dz");
    const msg = document.getElementById("msg");
    const pgWrap = document.getElementById("pgWrap");
    const pg = document.getElementById("pg");

    const lb = document.getElementById("lb");
    const lbImg = document.getElementById("lbImg");
    const lbClose = document.getElementById("lbClose");

    let loaded = new Set();

    function notify(text, ok=true){
      msg.textContent = text;
      msg.style.color = ok ? "#a7f3d0" : "#ffb0b0";
    }

    async function loadImages() {
      try{
        const res = await fetch("/api/images", {cache:"no-store"});
        const images = await res.json();
        images.forEach(img => {
          if (!loaded.has(img)) {
            const url = "/uploads/" + encodeURIComponent(img);

            const card = document.createElement("div");
            card.className = "card";
            const image = document.createElement("img");
            image.className = "thumb";
            image.loading = "lazy";
            image.src = url;

            const badge = document.createElement("div");
            badge.className = "badge";
            badge.textContent = img.split("_")[0]; // التاريخ من الاسم

            card.appendChild(image);
            card.appendChild(badge);
            gallery.prepend(card); // الأحدث يظهر الأول
            loaded.add(img);

            // Lightbox
            card.addEventListener("click", ()=>{
              lbImg.src = url;
              lb.classList.add("open");
            });
          }
        });
      }catch(e){
        console.error(e);
      }
    }

    function uploadFile(file){
      const form = new FormData();
      form.append("imageFile", file);

      pgWrap.style.display = "block";
      pg.style.width = "0%";
      notify("جاري الرفع…");

      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/upload", true);

      xhr.upload.onprogress = (e)=>{
        if(e.lengthComputable){
          const pct = Math.round((e.loaded/e.total)*100);
          pg.style.width = pct + "%";
        }
      };

      xhr.onload = ()=>{
        try{
          const res = JSON.parse(xhr.responseText || "{}");
          if(xhr.status === 200 && res.ok){
            notify("تم الرفع بنجاح ✓", true);
            pg.style.width = "100%";
            // حمّل الصورة الجديدة مباشرة
            loaded.delete(res.filename); // لضمان إضافتها
            loadImages();
          }else{
            notify(res.msg || "فشل الرفع", false);
          }
        }catch{
          notify("فشل الرفع", false);
        }
        setTimeout(()=>{ pgWrap.style.display = "none"; }, 900);
      };

      xhr.onerror = ()=>{ notify("خطأ في الاتصال", false); pgWrap.style.display = "none"; };

      xhr.send(form);
    }

    btnUpload.addEventListener("click", ()=>{
      const f = fileInput.files && fileInput.files[0];
      if(!f) return notify("اختاري صورة أولاً", false);
      uploadFile(f);
    });
    fileInput.addEventListener("change", (e)=>{
      if(e.target.files && e.target.files[0]){
        uploadFile(e.target.files[0]);
      }
    });

    // Drag & drop
    ;["dragenter","dragover"].forEach(ev => dz.addEventListener(ev, (e)=>{
      e.preventDefault(); e.stopPropagation(); dz.classList.add("dragover");
    }));
    ;["dragleave","drop"].forEach(ev => dz.addEventListener(ev, (e)=>{
      e.preventDefault(); e.stopPropagation(); dz.classList.remove("dragover");
    }));
    dz.addEventListener("drop", (e)=>{
      const f = e.dataTransfer.files && e.dataTransfer.files[0];
      if(f) uploadFile(f);
    });

    // Lightbox close
    lbClose.onclick = ()=> lb.classList.remove("open");
    lb.addEventListener("click", (e)=>{ if(e.target===lb) lb.classList.remove("open"); });

    // Initial + auto refresh
    loadImages();
    setInterval(loadImages, 5000);
  </script>
</body>
</html>
    """
    return render_template_string(html, year=datetime.now().year)

# ------------------------- Entrypoint -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)