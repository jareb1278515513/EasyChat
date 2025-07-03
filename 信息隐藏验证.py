from PIL import Image

def extract_message_from_image(image_path):
    """
    根据steganography.js的逻辑，从图片中提取隐藏的文本信息。
    
    Args:
        image_path (str): 隐写图片的路径。

    Returns:
        str: 提取到的隐藏信息，如果出错则返回错误信息。
    """
    try:
        img = Image.open(image_path)
        # 确保图像为RGBA模式，虽然JS脚本不修改A通道，但getImageData返回的是RGBA
        # 并且为了保持像素数据的顺序一致，我们处理RGBA
        img = img.convert("RGBA") 
    except FileNotFoundError:
        return "错误：图片文件未找到。"
    except Exception as e:
        return f"错误：无法加载图片 - {e}"

    width, height = img.size
    binary_message_bits = []
    
    # 遍历每个像素，并按照JS脚本的逻辑提取R, G, B通道的最低有效位
    # JS脚本中的 data 数组是 [R1, G1, B1, A1, R2, G2, B2, A2, ...]
    # 并且它是通过 dataIndex % 3 来确定是R, G, 还是B，跳过A
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = img.getpixel((x, y)) # 获取RGBA值

            # 提取R通道的LSB
            binary_message_bits.append(str(r & 1))
            # 提取G通道的LSB
            binary_message_bits.append(str(g & 1))
            # 提取B通道的LSB
            binary_message_bits.append(str(b & 1))

    # 将所有提取到的比特拼接成一个完整的二进制字符串
    full_binary_string = "".join(binary_message_bits)

    extracted_chars = []
    i = 0
    while True:
        # 每个字符是16位
        if i + 16 > len(full_binary_string):
            # 即使没有找到哨兵，也可能因为信息未满16位而结束
            break 
        
        char_binary = full_binary_string[i : i + 16]
        char_code = int(char_binary, 2)
        
        if char_code == 0: # 检查哨兵字符 '\0'
            break
        
        try:
            # 使用chr()从UTF-16编码的码点转换为字符
            extracted_chars.append(chr(char_code))
        except ValueError:
            # 如果解码失败，说明数据可能被破坏或不是预期的UTF-16编码
            # 可以选择跳过，或者返回当前已成功解码的部分
            print(f"警告：无法解码字符编码 {char_code}，可能遇到非预期的二进制数据。")
            break # 遇到无法解码的字符就停止
        
        i += 16
            
    return "".join(extracted_chars)

if __name__ == "__main__":
    # 请替换为你的隐写图片路径
    # 假设你有一个名为 'steg_image.png' 的图片在当前目录下
    image_file_path = "D:/下载/121.png"
    
    hidden_message = extract_message_from_image(image_file_path)
    
    if hidden_message.startswith("错误"):
        print(hidden_message)
    else:
        print(f"成功提取到隐藏信息：\n{hidden_message}")