import axios from 'axios';

const apiKey = process.env.VUE_APP_DEEPSEEK_API_KEY;
const baseURL = 'https://api.deepseek.com/v1';

const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${apiKey}`,
  },
});

/**
 * Gets a reply from the DeepSeek AI model.
 * @param {Array<{role: string, content: string}>} messages - The conversation history.
 * @returns {Promise<string>} - The AI's response message.
 */
export async function getAiReply(messages) {
  if (!apiKey || apiKey === "sk-your-deepseek-api-key-here") {
    const errorMessage = 'DeepSeek API key is not configured. Please create a .env.local file in the "frontend" directory and set your VUE_APP_DEEPSEEK_API_KEY.';
    console.error(errorMessage);
    // Return the error message to be displayed in the chat window
    return Promise.resolve(errorMessage);
  }

  try {
    const response = await apiClient.post('/chat/completions', {
      model: 'deepseek-chat',
      messages: messages,
      stream: false,
    });

    if (response.data && response.data.choices && response.data.choices[0].message) {
      return response.data.choices[0].message.content;
    } else {
      throw new Error('Invalid response format from DeepSeek API.');
    }
  } catch (error) {
    const errorMessage = error.response ? error.response.data.error.message : error.message;
    console.error('Error calling DeepSeek API:', errorMessage);
    // Return a user-friendly error message
    return Promise.resolve(`抱歉，AI助手出错了: ${errorMessage}`);
  }
} 