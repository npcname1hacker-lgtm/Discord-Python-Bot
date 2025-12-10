// ɢʀᴠ戰隊管理系統 - 主要JavaScript功能

// 全局配置
const API_BASE_URL = '';

// 通用API請求函數
async function apiRequest(method, url, data = null) {
    const config = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data) {
        config.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, config);
        return await response.json();
    } catch (error) {
        console.error('API請求錯誤:', error);
        throw error;
    }
}

// 顯示通知
function showNotification(message, type = 'info') {
    const alertClass = type === 'error' ? 'alert-danger' : 
                      type === 'success' ? 'alert-success' : 'alert-info';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('main .container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // 5秒後自動隱藏
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }, 5000);
    } else {
        // 如果找不到容器，使用alert
        alert(message);
    }
}

// 確認對話框
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 表單驗證
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    
    for (let input of inputs) {
        if (!input.value.trim()) {
            input.focus();
            showNotification('請填寫所有必填欄位', 'error');
            return false;
        }
    }
    
    return true;
}

// 密碼確認驗證
function validatePasswordMatch(password1Id, password2Id) {
    const password1 = document.getElementById(password1Id).value;
    const password2 = document.getElementById(password2Id).value;
    
    if (password1 !== password2) {
        showNotification('兩次輸入的密碼不一致', 'error');
        return false;
    }
    
    return true;
}

// 初始化功能
document.addEventListener('DOMContentLoaded', function() {
    // 為所有表單添加Enter鍵提交
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const submitBtn = form.querySelector('button[type="submit"], .btn-primary');
                if (submitBtn) {
                    submitBtn.click();
                }
            }
        });
    });
    
    // 自動隱藏警告訊息
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            if (alert.classList.contains('show')) {
                alert.classList.remove('show');
            }
        });
    }, 5000);
});

// 機器人控制功能
async function sendBotMessage() {
    if (!validateForm('botSayForm')) return;
    
    const channel = document.getElementById('channelSelect').value;
    const message = document.getElementById('botMessage').value;
    
    try {
        const result = await apiRequest('POST', '/api/bot/say', {
            channel_id: channel,
            message: message
        });
        
        if (result.success) {
            showNotification('訊息已發送！', 'success');
            document.getElementById('botMessage').value = '';
        } else {
            showNotification('發送失敗：' + result.error, 'error');
        }
    } catch (error) {
        showNotification('網路錯誤，請稍後再試', 'error');
    }
}

// 複製到剪貼板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('已複製到剪貼板', 'success');
    }).catch(() => {
        showNotification('複製失敗', 'error');
    });
}

// 格式化時間
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 頁面載入動畫
function addFadeInAnimation() {
    document.querySelectorAll('.card, .alert').forEach((element, index) => {
        element.style.animationDelay = `${index * 0.1}s`;
        element.classList.add('fade-in');
    });
}