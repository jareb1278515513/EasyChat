// A simple steganography implementation using LSB encoding on a canvas.

/**
 * Hides a text message within an image.
 * @param {File} imageFile The image file to hide the message in.
 * @param {string} message The text message to hide.
 * @returns {Promise<string>} A promise that resolves with the data URL of the new image.
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

                // Use a sentinel to mark the end of the message
                const fullMessage = message + '\0'; // Null character as sentinel
                const binaryMessage = messageToBinary(fullMessage);

                // Check if the message is too long for the image (3 bits per pixel for RGB)
                if (binaryMessage.length > data.length / 8 * 3) {
                    return reject(new Error('消息对于此图像来说太长。'));
                }

                let dataIndex = 0;
                for (let i = 0; i < binaryMessage.length; i++) {
                    const bit = parseInt(binaryMessage[i]);

                    // Modify the LSB of the color channel, skipping the alpha channel
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
 * Extracts a hidden message from an image data URL.
 * @param {string} imageUrl The data URL of the image.
 * @returns {Promise<string>} A promise that resolves with the hidden message.
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
            // eslint-disable-next-line no-constant-condition
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
                if (charCode === 0) { // Check for null sentinel
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

function messageToBinary(message) {
    let binary = '';
    for (let i = 0; i < message.length; i++) {
        const charCode = message.charCodeAt(i);
        binary += charCode.toString(2).padStart(16, '0'); // Use 16 bits for UTF-16 characters
    }
    return binary;
}

function binaryToMessage(binary) {
    let message = '';
    for (let i = 0; i < binary.length; i += 16) {
        const binaryChar = binary.substr(i, 16);
        const charCode = parseInt(binaryChar, 2);
        message += String.fromCharCode(charCode);
    }
    return message;
} 