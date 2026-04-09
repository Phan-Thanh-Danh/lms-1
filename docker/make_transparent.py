from PIL import Image
import os

def make_transparent(img_path):
    if not os.path.exists(img_path):
        print(f"File not found: {img_path}")
        return

    img = Image.open(img_path)
    img = img.convert("RGBA")

    datas = img.getdata()

    new_data = []
    # Ngưỡng (threshold) để xác định màu trắng (vì trắng có khi không phải là 255, 255, 255 tuyệt đối)
    threshold = 230
    
    for item in datas:
        # Nếu R, G, B đều > threshold thì coi là nền trắng và chuyển sang trong suốt
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(img_path, "PNG")
    print(f"SUCCESS: {img_path} is now transparent.")

if __name__ == "__main__":
    # Đường dẫn trong container (mounted từ /home/loc/LMS_NEW/docker)
    target_path = "/workspace/MOCCHUNGCHI.png"
    make_transparent(target_path)
