import os
import math
import pyvips

pics_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')

max_pixels = 320 * 240
image = pyvips.Image.new_from_file(pics_dir + '/111.png', access='sequential')
current_pixels = image.width * image.height

if current_pixels <= max_pixels:
    print(f"图像已满足像素限制 ({current_pixels} ≤ {max_pixels})")
    exit()

# 计算缩放比例（保持宽高比）
scale_factor = math.sqrt(max_pixels / current_pixels)
thumbnail = image.resize(scale_factor, kernel="cubic")
thumbnail.write_to_file('thumbnail.jpg')
