/**
 * 基于Canvas的LSB隐写实现在图像中隐藏文本信息
 */

/**
 * 在图像中隐藏文本信息
 * @param {File} imageFile 要隐藏信息的图像文件
 * @param {string} message 要隐藏的文本信息
 * @returns {Promise<string>} 返回包含隐藏信息的新图像数据URL
 */
export function hideMessage(imageFile, message) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext('2d');
                if (!ctx) {
                    return reject(new Error('Unable to get canvas context.'));
                }
                ctx.drawImage(img, 0, 0);

                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const data = imageData.data;

                // 使用一个哨兵来标记信息的结束
                const fullMessage = message + '\0'; //  NULL作为哨兵结束信息
                const binaryMessage = messageToBinary(fullMessage);

                // 检查消息长度是否超过图像容量
                if (binaryMessage.length > data.length / 8 * 3) {
                    return reject(new Error('消息对于此图像来说太长。'));
                }

                let dataIndex = 0;
                for (let i = 0; i < binaryMessage.length; i++) {
                    const bit = parseInt(binaryMessage[i]);

                    // 按位修改图像数据，跳过透明通道
                    const pixelIndex = Math.floor(dataIndex / 3);
                    const channelIndex = dataIndex % 3;
                    const absoluteIndex = pixelIndex * 4 + channelIndex;

                    if (absoluteIndex >= data.length) {
                        return reject(new Error('在编码过程中图像数据溢出。'));
                    }

                    data[absoluteIndex] = (data[absoluteIndex] & 0xFE) | bit;
                    dataIndex++;
                }

                ctx.putImageData(imageData, 0, 0);
                resolve(canvas.toDataURL('image/png'));
            };
            img.onerror = () => reject(new Error('无法加载图像。'));
            img.src = e.target.result;
        };
        reader.onerror = () => reject(new Error('无法读取文件。'));
        reader.readAsDataURL(imageFile);
    });
}

/**
 * 从图像数据URL中提取隐藏信息
 * @param {string} imageUrl 包含隐藏信息的图像数据URL
 * @returns {Promise<string>} 返回提取出的隐藏信息
 */
export function extractMessage(imageUrl) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            if (!ctx) {
                return reject(new Error('无法获取画布上下文。'));
            }
            ctx.drawImage(img, 0, 0);

            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            let binaryMessage = '';
            let charCode = null;

            let dataIndex = 0;

            // 循环直到遇到哨兵字符NULL
            while (true) {
                let binaryChar = '';
                for (let i = 0; i < 16; i++) { // 16 bits per character
                    const pixelIndex = Math.floor(dataIndex / 3);
                    const channelIndex = dataIndex % 3;
                    const absoluteIndex = pixelIndex * 4 + channelIndex;

                    if (absoluteIndex >= data.length) {
                        return reject(new Error('在读取消息时图像数据溢出。'));
                    }
                    binaryChar += (data[absoluteIndex] & 1).toString();
                    dataIndex++;
                }

                charCode = parseInt(binaryChar, 2);
                if (charCode === 0) {
                    break;
                }
                binaryMessage += binaryChar;
            }

            resolve(binaryToMessage(binaryMessage));
        };
        img.onerror = () => reject(new Error('无法加载图像。'));
        img.src = imageUrl;
    });
}

/**
 * 将文本信息转换为二进制字符串
 * @param {string} message 要转换的文本信息
 * @returns {string} 返回16位二进制字符串
 */
function messageToBinary(message) {
    let binary = '';
    for (let i = 0; i < message.length; i++) {
        const charCode = message.charCodeAt(i);
        binary += charCode.toString(2).padStart(16, '0');
    }
    return binary;
}

/**
 * 将二进制字符串转换回文本信息
 * @param {string} binary 二进制字符串
 * @returns {string} 返回转换后的文本信息
 */
function binaryToMessage(binary) {
    let message = '';
    for (let i = 0; i < binary.length; i += 16) {
        const binaryChar = binary.substr(i, 16);
        const charCode = parseInt(binaryChar, 2);
        message += String.fromCharCode(charCode);
    }
    return message;
} 