from io import BytesIO
from PIL import Image
import base64

def pil_to_b64(img):
    buf = BytesIO()
    img.save(buf, format="PNG")
    # default codec is utf-8
    return base64.b64encode(buf.getvalue()).decode()

def b64_to_pil(b64_str):
    return Image.open(BytesIO(base64.b64decode(b64_str)))

if __name__ == "__main__":
    # Example usage
    img = Image.open("../data/elinor.jpeg")
    img_str = pil_to_b64(img)
    print("Encoded string:", img_str)
    
    decoded_img = b64_to_pil(img_str)
    decoded_img.show()