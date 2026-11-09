import json

def build_auth_lite_css():
    return r"""
    <style>
        /* 1. LỚP NỀN ĐEN CHE TOÀN BỘ TRANG WEB */
        #authOverlay { 
            position: fixed; inset: 0; z-index: 999999; 
            background: rgba(15, 23, 42, 0.95); 
            backdrop-filter: blur(10px); 
            display: none; align-items: center; justify-content: center; 
            padding: 1rem; font-family: system-ui, -apple-system, sans-serif; 
            overflow-y: auto;
        }
        #authOverlay.show { display: flex; }

        /* 2. KHÓA CUỘN TRANG WEB KHI MODAL ĐANG MỞ */
        body.auth-active { overflow: hidden !important; }
        
        /* 3. HỘP ĐĂNG NHẬP (CSS THUẦN) */
        .auth-box { 
            background: #1e293b; border: 1px solid #334155; 
            border-radius: 16px; width: 100%; max-width: 400px; 
            padding: 2rem; box-shadow: 0 25px 50px -12px rgba(0,0,0,.8); 
            text-align: center; color: #f1f5f9; position: relative; 
            box-sizing: border-box; margin: auto;
            animation: slideUp .3s ease; 
        }
        @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        
        .auth-title { font-size: 1.25rem; font-weight: 800; margin-bottom: 0.5rem; color: #fff; }
        .auth-sub { font-size: 0.85rem; color: #94a3b8; margin-bottom: 1.5rem; line-height: 1.5; }
        
        .btn-google { display: flex; align-items: center; justify-content: center; gap: 0.75rem; width: 100%; padding: 0.75rem; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; font-weight: 600; font-size: 0.9rem; cursor: pointer; transition: 0.2s; margin-bottom: 1rem; }
        .btn-google:hover { background: #1e293b; border-color: #64748b; }
        
        .auth-divider { display: flex; align-items: center; gap: 0.5rem; margin: 1rem 0; color: #64748b; font-size: 0.75rem; font-weight: 600; }
        .auth-divider::before, .auth-divider::after { content: ''; flex: 1; height: 1px; background: #334155; }
        
        .auth-input { width: 100%; padding: 0.75rem; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; font-size: 0.9rem; outline: none; margin-bottom: 0.75rem; transition: 0.2s; font-family: inherit; box-sizing: border-box; }
        .auth-input:focus { border-color: #10b981; box-shadow: 0 0 0 2px rgba(16,185,129,0.2); }
        
        .auth-btn { width: 100%; padding: 0.75rem; border-radius: 8px; background: #10b981; color: #fff; font-weight: 700; font-size: 0.9rem; border: none; cursor: pointer; transition: 0.2s; display: flex; align-items: center; justify-content: center; gap: 0.5rem; font-family: inherit; box-sizing: border-box; }
        .auth-btn:hover { background: #059669; }
        .auth-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .auth-btn.outline { background: transparent; border: 1px solid #475569; color: #cbd5e1; }
        .auth-btn.outline:hover { background: #334155; color: #fff; }
        
        .auth-link { color: #38bdf8; font-size: 0.8rem; cursor: pointer; background: none; border: none; padding: 0; margin-top: 0.5rem; text-decoration: none; font-family: inherit; }
        .auth-link:hover { color: #7dd3fc; text-decoration: underline; }
        
        .auth-msg { padding: 0.75rem; border-radius: 8px; font-size: 0.8rem; margin-top: 1rem; display: none; text-align: left; line-height: 1.4; }
        .auth-msg.show { display: block; }
        .auth-msg.error { background: rgba(244,63,94,.15); color: #fda4af; border: 1px solid rgba(244,63,94,.3); }
        .auth-msg.success { background: rgba(16,185,129,.15); color: #6ee7b7; border: 1px solid rgba(16,185,129,.3); }
        
        /* Các modal phụ */
        #setPwdModal { display: none; position: fixed; inset: 0; z-index: 1000000; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(8px); align-items: center; justify-content: center; padding: 1rem; }
        #renewalModal { position: fixed; inset: 0; z-index: 1000001; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(8px); display: none; align-items: center; justify-content: center; padding: 1rem; font-family: system-ui, -apple-system, sans-serif; }
        #renewalModal.show { display: flex; }
        .renewal-box { background: #1e293b; border: 1px solid #334155; border-radius: 20px; width: 100%; max-width: 450px; padding: 2rem; text-align: center; position: relative; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.8); animation: slideUp .3s ease; max-height: 95vh; overflow-y: auto; }
        .renewal-icon { width: 64px; height: 64px; border-radius: 50%; background: rgba(244,63,94,0.15); color: #f43f5e; display: flex; align-items: center; justify-content: center; font-size: 1.75rem; margin: 0 auto 1rem; border: 2px solid rgba(244,63,94,0.3); }
        .package-item { border: 1px solid #475569; border-radius: 8px; padding: 12px; margin-bottom: 8px; cursor: pointer; text-align: left; transition: 0.2s; display: flex; justify-content: space-between; align-items: center; background: #0f172a; }
        .package-item:hover { border-color: #64748b; }
        .package-item.active { border-color: #10b981; background: rgba(16,185,129,0.1); }
        .bank-info { background: #0f172a; border: 1px dashed #334155; border-radius: 12px; padding: 1rem; margin: 1rem 0; text-align: left; font-size: 0.85rem; }
        .bank-row { display: flex; justify-content: space-between; margin-bottom: 0.5rem; align-items: center; }
        .bank-row:last-child { margin-bottom: 0; }
        .bank-row span:first-child { color: #94a3b8; }
        .bank-row span:last-child { font-weight: 700; color: #fff; }
        .code-highlight { color: #10b981 !important; font-family: monospace; font-size: 1.1rem; letter-spacing: 1px; background: rgba(16,185,129,0.1); padding: 2px 8px; border-radius: 4px; }
    </style>
    """

def build_auth_lite_html(config):
    bank = config.get("bank_config", {})
    packages = config.get("packages", [])
    packages_html = ""
    for p in packages:
        save_badge = f'<span style="background:#10b981;color:#fff;font-size:10px;padding:2px 6px;border-radius:4px;margin-left:8px;">{p["save"]}</span>' if p.get("save") else ""
        packages_html += f"""
        <div onclick="selectPackage('{p['id']}', {p['amount']}, '{p['label']}')" class="package-item" id="pkg_{p['id']}">
            <div><div style="font-weight:bold; color:#fff; font-size:0.9rem;">{p['label']} {save_badge}</div></div>
            <div style="color:#10b981; font-weight:bold;">{p['amount']:,}đ</div>
        </div>
        """
    return f"""
    <div id="authOverlay" class="show">
        <div class="auth-box">
            <div class="auth-title">Đăng nhập hệ thống</div>
            <div class="auth-sub">Sử dụng tài khoản để truy cập Pro Quant Screener</div>
            
            <button class="btn-google" id="btnGoogleLogin">
                <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="20" height="20">
                Đăng nhập bằng Google
            </button>
            
            <div class="auth-divider">HOẶC</div>
            
            <form id="emailLoginForm">
                <input type="text" id="loginEmail" class="auth-input" placeholder="Email (VD: abc@gmail.com)" autocomplete="email">
                <input type="password" id="loginPassword" class="auth-input" placeholder="Mật khẩu" autocomplete="current-password">
                <div id="loginMsg" class="auth-msg"></div>
                <button type="submit" class="auth-btn" id="btnEmailLogin" style="margin-top:1rem;">
                    <i class="fa-solid fa-sign-in-alt"></i> <span>Đăng nhập</span>
                </button>
                <div style="display:flex; justify-content:space-between; margin-top:0.5rem;">
                    <button type="button" class="auth-link" onclick="forgotPassword()">Quên mật khẩu?</button>
                    <button type="button" class="auth-link" onclick="showRegisterForm()">Tạo tài khoản</button>
                </div>
            </form>
        </div>
    </div>
    
    <div id="setPwdModal">
        <div class="auth-box">
            <div class="auth-title">Tạo mật khẩu dự phòng</div>
            <div class="auth-sub">Bạn đang đăng nhập bằng Google. Hãy tạo mật khẩu để lần sau có thể đăng nhập bằng Email.</div>
            <input type="password" id="newPwd1" class="auth-input" placeholder="Mật khẩu mới (tối thiểu 6 ký tự)">
            <input type="password" id="newPwd2" class="auth-input" placeholder="Nhập lại mật khẩu">
            <div id="setPwdMsg" class="auth-msg"></div>
            <button class="auth-btn" id="btnSavePwd" style="margin-top:1rem;">Lưu mật khẩu</button>
            <button class="auth-link" id="btnSkipPwd" style="margin-top:1rem; display:block; width:100%;">Để sau</button>
        </div>
    </div>
    
    <div id="renewalModal">
        <div class="renewal-box">
            <button class="auth-close" onclick="auth.signOut()" title="Đăng xuất" style="position:absolute;top:1rem;right:1rem;background:none;border:none;color:#94a3b8;font-size:1.25rem;cursor:pointer;">✕</button>
            <div class="renewal-icon"><i class="fa-solid fa-clock"></i></div>
            <h2 class="auth-title" style="color:#f43f5e;">Tài khoản đã hết hạn!</h2>
            <p class="auth-sub">Thời gian dùng thử đã kết thúc. Vui lòng chọn gói để tiếp tục sử dụng.</p>
            <div style="text-align:left; margin-bottom:10px; font-weight:bold; color:#94a3b8; font-size:0.8rem;">CHỌN GÓI GIA HẠN:</div>
            <div style="max-height:200px; overflow-y:auto; padding-right:5px;" id="packageList">{packages_html}</div>
            <div id="qrCodeWrap" style="display:none; margin-top:1rem;">
                <img id="qrImage" src="" style="width:200px; height:200px; margin:0 auto 10px; border-radius:12px; border:2px solid #334155; background:#fff; padding: 5px;">
                <div class="bank-info">
                    <div class="bank-row"><span>Ngân hàng:</span> <span>{bank.get('bank_name', 'MB Bank')}</span></div>
                    <div class="bank-row"><span>Số TK:</span> <span>{bank.get('account_no', '0123456789')}</span></div>
                    <div class="bank-row"><span>Chủ TK:</span> <span>{bank.get('account_name', 'NGUYEN VAN A')}</span></div>
                    <div class="bank-row"><span>Số tiền:</span> <span id="payAmount" class="code-highlight">0 VNĐ</span></div>
                    <div class="bank-row"><span>Nội dung:</span> <span id="payCode" class="code-highlight">---</span></div>
                </div>
                <p style="font-size:0.75rem; color:#f59e0b; text-align:left; margin-bottom:10px;"><i class="fa-solid fa-info-circle"></i> Vui lòng chuyển khoản đúng nội dung.</p>
            </div>
            <div style="display:flex; gap:10px; margin-top:1rem;">
                <button class="auth-btn outline" onclick="auth.signOut()">Đăng xuất</button>
                <button class="auth-btn" id="btnConfirmPay" style="display:none;" onclick="confirmPayment()">Tôi đã chuyển khoản</button>
            </div>
        </div>
    </div>
    """

def build_auth_lite_js(config):
    trial_days = config.get("trial_days", 7)
    bank_config_js = json.dumps(config.get("bank_config", {}), ensure_ascii=False)
    
    return f"""
    <script>
    (function() {{
        'use strict';
        var TRIAL_DAYS = {trial_days};
        var BANK_CONFIG = {bank_config_js};
        var selectedPkgId = null;
        var selectedAmount = 0;
        
        // Hàm chờ Firebase tải xong
        function waitAuth(cb) {{
            var t = setInterval(function() {{
                if (typeof firebase !== 'undefined' && typeof window.auth !== 'undefined' && typeof window.db !== 'undefined') {{
                    clearInterval(t); cb();
                }}
            }}, 200);
        }}

        // Khóa cuộn trang ngay lập tức khi vừa vào web
        document.body.classList.add('auth-active');

        waitAuth(function() {{
            var auth = window.auth;
            var db = window.db;

            auth.onAuthStateChanged(async function(user) {{
                if (user) {{
                    // NẾU ĐÃ ĐĂNG NHẬP: Mở khóa trang
                    document.body.classList.remove('auth-active');
                    document.getElementById('authOverlay').classList.remove('show');
                    
                    await checkUserPermission(user);
                    if (typeof window.onAuthReady === 'function') {{
                        try {{ await window.onAuthReady(user); }} catch(e) {{ console.warn('onAuthReady error:', e); }}
                    }}
                }} else {{
                    // NẾU CHƯA ĐĂNG NHẬP: Khóa trang và hiện form
                    document.body.classList.add('auth-active');
                    document.getElementById('authOverlay').classList.add('show');
                    document.getElementById('renewalModal').classList.remove('show');
                    selectedPkgId = null;
                }}
            }});

            document.getElementById('btnGoogleLogin').addEventListener('click', async function() {{
                var provider = new firebase.auth.GoogleAuthProvider();
                try {{
                    var res = await auth.signInWithPopup(provider);
                    if (res.user) checkAskPassword(res.user);
                }} catch(e) {{ showMsg('loginMsg', 'Lỗi Google: ' + e.message, 'error'); }}
            }});

            var loginForm = document.getElementById('emailLoginForm');
            var emailInput = document.getElementById('loginEmail');
            
            emailInput.addEventListener('blur', function() {{
                var v = this.value.trim().toLowerCase();
                if (v && v.indexOf('@') === -1) this.value = v + '@gmail.com';
            }});

            loginForm.addEventListener('submit', async function(e) {{
                e.preventDefault();
                var email = emailInput.value.trim();
                var pwd = document.getElementById('loginPassword').value;
                var btn = document.getElementById('btnEmailLogin');
                var btnSpan = btn.querySelector('span');
                var msgBox = document.getElementById('loginMsg');
                
                // Reset thông báo cũ
                msgBox.className = 'auth-msg';
                msgBox.innerHTML = '';

                if (!email || !pwd) return showMsg('loginMsg', 'Vui lòng nhập đủ email và mật khẩu.', 'error');
                
                btn.disabled = true; 
                btnSpan.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang kết nối...';
                
                try {{
                    await auth.signInWithEmailAndPassword(email, pwd);
                    // Đăng nhập thành công thì onAuthStateChanged sẽ tự xử lý
                }} catch(e) {{
                    // Hiển thị lỗi rõ ràng
                    var errMsg = e.message;
                    if (e.code === 'auth/user-not-found') errMsg = 'Tài khoản này chưa tồn tại. Vui lòng đăng nhập bằng Google hoặc bấm "Tạo tài khoản".';
                    if (e.code === 'auth/wrong-password') errMsg = 'Sai mật khẩu. Vui lòng kiểm tra lại.';
                    
                    showMsg('loginMsg', 'Lỗi: ' + errMsg, 'error');
                    btn.disabled = false; 
                    btnSpan.innerHTML = 'Đăng nhập';
                }}
            }});

            function checkAskPassword(user) {{
                if (!user || !user.email) return;
                var hasPwd = user.providerData.some(function(p) {{ return p.providerId === 'password'; }});
                if (hasPwd || sessionStorage.getItem('asked_pwd_' + user.email)) return;
                sessionStorage.setItem('asked_pwd_' + user.email, '1');
                document.getElementById('setPwdModal').style.display = 'flex';
            }}

            document.getElementById('btnSkipPwd').addEventListener('click', function() {{
                document.getElementById('setPwdModal').style.display = 'none';
            }});

            document.getElementById('btnSavePwd').addEventListener('click', async function() {{
                var p1 = document.getElementById('newPwd1').value;
                var p2 = document.getElementById('newPwd2').value;
                if (p1.length < 6) return showMsg('setPwdMsg', 'Mật khẩu phải từ 6 ký tự.', 'error');
                if (p1 !== p2) return showMsg('setPwdMsg', 'Mật khẩu nhập lại không khớp.', 'error');
                
                var btn = this; btn.disabled = true; btn.innerText = 'Đang lưu...';
                try {{
                    var user = auth.currentUser;
                    var cred = firebase.auth.EmailAuthProvider.credential(user.email, p1);
                    await user.linkWithCredential(cred);
                    showMsg('setPwdMsg', '✅ Tạo mật khẩu thành công!', 'success');
                    setTimeout(function() {{ document.getElementById('setPwdModal').style.display = 'none'; }}, 1500);
                }} catch(e) {{
                    showMsg('setPwdMsg', 'Lỗi: ' + e.message, 'error');
                    btn.disabled = false; btn.innerText = 'Lưu mật khẩu';
                }}
            }});

            async function checkUserPermission(user) {{
                var email = user.email.toLowerCase();
                try {{
                    var doc = await db.collection('allowed_users').doc(email).get();
                    if (!doc.exists) {{
                        var expireDate = new Date();
                        expireDate.setDate(expireDate.getDate() + TRIAL_DAYS);
                        await db.collection('allowed_users').doc(email).set({{
                            email: email, role: 'user', expiresAt: expireDate.toISOString()
                        }});
                        alert('Chào mừng bạn! Bạn được dùng thử ' + TRIAL_DAYS + ' ngày.');
                    }} else {{
                        var data = doc.data();
                        if (data.role !== 'admin' && data.expiresAt) {{
                            var exp = new Date(data.expiresAt);
                            if (new Date() > exp) {{
                                document.body.classList.remove('auth-active');
                                document.getElementById('renewalModal').classList.add('show');
                                document.getElementById('authOverlay').classList.remove('show');
                            }} else {{
                                document.getElementById('renewalModal').classList.remove('show');
                            }}
                        }}
                    }}
                }} catch(e) {{ console.warn('Lỗi check quyền:', e); }}
            }}

            window.selectPackage = function(id, amount, label) {{
                selectedPkgId = id;
                selectedAmount = amount;
                document.querySelectorAll('.package-item').forEach(function(el) {{ el.classList.remove('active'); }});
                var el = document.getElementById('pkg_' + id);
                if (el) el.classList.add('active');
                document.getElementById('qrCodeWrap').style.display = 'block';
                document.getElementById('payAmount').innerText = amount.toLocaleString('vi-VN') + ' VNĐ';
                var code = 'NAP' + Math.floor(100000 + Math.random() * 900000);
                document.getElementById('payCode').innerText = code;
                var qrUrl = `https://img.vietqr.io/image/${{BANK_CONFIG.bank_id}}-${{BANK_CONFIG.account_no}}-compact2.png?amount=${{amount}}&addInfo=${{code}}&accountName=${{encodeURIComponent(BANK_CONFIG.account_name)}}`;
                document.getElementById('qrImage').src = qrUrl;
                document.getElementById('btnConfirmPay').style.display = 'flex';
            }};

            window.confirmPayment = async function() {{
                if (!selectedPkgId) return;
                if (!auth.currentUser) return alert('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.');
                var btn = document.getElementById('btnConfirmPay');
                btn.disabled = true; btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang gửi...';
                try {{
                    await db.collection('renewal_requests').add({{
                        email: auth.currentUser.email,
                        packageId: selectedPkgId,
                        amount: selectedAmount,
                        code: document.getElementById('payCode').innerText,
                        status: 'pending',
                        createdAt: firebase.firestore.FieldValue.serverTimestamp()
                    }});
                    alert('Đã gửi yêu cầu! Vui lòng đợi Admin xác nhận.');
                    btn.innerText = 'Đã gửi thành công';
                    btn.style.background = '#059669';
                    selectedPkgId = null;
                }} catch(e) {{
                    alert('Lỗi gửi yêu cầu: ' + e.message);
                    btn.disabled = false; btn.innerText = 'Tôi đã chuyển khoản';
                }}
            }};

            window.showRegisterForm = function() {{ alert('Vui lòng đăng nhập bằng Google để tạo tài khoản tự động!'); }};
            window.forgotPassword = async function() {{
                var email = document.getElementById('loginEmail').value.trim();
                if (!email) return showMsg('loginMsg', 'Nhập email để lấy lại mật khẩu.', 'error');
                try {{
                    await auth.sendPasswordResetEmail(email);
                    showMsg('loginMsg', '✅ Đã gửi link khôi phục vào email!', 'success');
                }} catch(e) {{ showMsg('loginMsg', 'Lỗi: ' + e.message, 'error'); }}
            }};
            
            function showMsg(id, text, type) {{
                var el = document.getElementById(id);
                if(!el) return;
                el.className = 'auth-msg show ' + (type || 'error');
                el.innerHTML = text;
            }}
        }});
    }})();
    </script>
    """
