# -*- coding: utf-8 -*-
"""giaodien_auth.py — Module xác thực rút gọn (Auth Lite)."""

import json

def build_auth_lite_css():
    return r"""
    <style>
        /* 1. NỀN ĐEN ĐẶC PHỦ KÍN 100% MÀN HÌNH - CĂN GIỮA TUYỆT ĐỐI TRÊN MỌI THIẾT BỊ */
        #authOverlay { 
            position: fixed !important; 
            inset: 0 !important; 
            width: 100vw !important; 
            height: 100vh !important; 
            z-index: 99999999 !important; 
            background: #0f172a !important; 
            display: flex !important; 
            align-items: center !important; 
            justify-content: center !important; 
            padding: 1rem !important; 
            box-sizing: border-box !important;
            overflow-y: auto !important;
            opacity: 1;
            visibility: visible;
            transition: opacity 0.25s ease, visibility 0.25s ease;
        }
        #authOverlay.hidden { 
            opacity: 0 !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }

        /* 2. HỘP ĐĂNG NHẬP LUÔN NẰM CHÍNH GIỮA CẢ PC VÀ MOBILE */
        .auth-box { 
            background: linear-gradient(145deg, #1e293b, #0f172a); 
            border: 1px solid rgba(51, 65, 85, 0.8); 
            border-radius: 20px; 
            width: 100%; 
            max-width: 400px; 
            padding: 2.5rem 2rem; 
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.05); 
            text-align: center; 
            color: #f1f5f9; 
            box-sizing: border-box;
            margin: auto !important; /* Đảm bảo căn giữa tuyệt đối trong flex container */
            transform: scale(1);
            transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        #authOverlay.hidden .auth-box {
            transform: scale(0.95);
        }
        
        .auth-title { font-size: 1.35rem; font-weight: 800; margin-bottom: 0.5rem; color: #fff; letter-spacing: -0.025em; }
        .auth-sub { font-size: 0.85rem; color: #94a3b8; margin-bottom: 1.75rem; line-height: 1.5; }
        
        .btn-google { 
            display: flex; align-items: center; justify-content: center; gap: 0.75rem; 
            width: 100%; padding: 0.85rem; border-radius: 12px; 
            border: 1px solid #475569; background: #0f172a; color: #fff; 
            font-weight: 600; font-size: 0.9rem; cursor: pointer; 
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); 
            margin-bottom: 1rem; 
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        .btn-google:hover { background: #1e293b; border-color: #64748b; transform: translateY(-1px); }
        
        .auth-divider { display: flex; align-items: center; gap: 0.75rem; margin: 1.25rem 0; color: #64748b; font-size: 0.75rem; font-weight: 600; }
        .auth-divider::before, .auth-divider::after { content: ''; flex: 1; height: 1px; background: #334155; }
        
        .auth-input { 
            width: 100%; padding: 0.85rem 1rem; border-radius: 12px; 
            border: 1px solid #334155; background: rgba(15, 23, 42, 0.6); 
            color: #fff; font-size: 0.9rem; outline: none; margin-bottom: 0.85rem; 
            box-sizing: border-box; transition: all 0.2s ease; 
        }
        .auth-input:focus { 
            border-color: #10b981; 
            background: rgba(15, 23, 42, 0.9);
            box-shadow: 0 0 0 3px rgba(16,185,129,0.15); 
        }
        
        .auth-btn { 
            width: 100%; padding: 0.85rem; border-radius: 12px; 
            background: #10b981; color: #fff; font-weight: 700; font-size: 0.9rem; 
            border: none; cursor: pointer; display: flex; align-items: center; 
            justify-content: center; gap: 0.5rem; box-sizing: border-box; 
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
        }
        .auth-btn:hover { background: #059669; transform: translateY(-1px); }
        
        .auth-link { color: #38bdf8; font-size: 0.8rem; cursor: pointer; background: none; border: none; padding: 0; margin-top: 0.75rem; text-decoration: none; }
        .auth-link:hover { color: #7dd3fc; text-decoration: underline; }
        
        .auth-msg { padding: 0.85rem; border-radius: 10px; font-size: 0.8rem; margin-top: 1rem; display: none; text-align: left; }
        .auth-msg.show { display: block; }
        .auth-msg.error { background: rgba(244,63,94,.12); color: #fda4af; border: 1px solid rgba(244,63,94,.25); }
        .auth-msg.success { background: rgba(16,185,129,.12); color: #6ee7b7; border: 1px solid rgba(16,185,129,.25); }

        /* MODAL GIA HẠN */
        #renewalModal { position: fixed; inset: 0; z-index: 10000001; background: rgba(15, 23, 42, 0.98); backdrop-filter: blur(12px); display: none; align-items: center; justify-content: center; padding: 1rem; font-family: system-ui, -apple-system, sans-serif; overflow-y: auto; }
        #renewalModal.show { display: flex; }
        .renewal-box { background: #1e293b; border: 1px solid #334155; border-radius: 20px; width: 100%; max-width: 450px; padding: 2rem; text-align: center; position: relative; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.8); margin: auto; max-height: 95vh; overflow-y: auto; }
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
    <!-- HIỂN THỊ HẠN DÙNG KÈM NÚT GIA HẠN CHỦ ĐỘNG CHO USER -->
    <div id="userExpireBadge" style="display:none; align-items: center; gap: 8px; font-size: 0.75rem;">
        <span style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 10px; border-radius: 6px; font-weight: bold;">
            <i class="fa-solid fa-clock"></i> <span id="expireDateText">Đang tải hạn dùng...</span>
        </span>
        <button onclick="openUserRenewalModal()" style="background: #10b981; color: #fff; border: none; padding: 5px 10px; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s;" title="Gia hạn tài khoản">
            <i class="fa-solid fa-plus-circle"></i> Gia hạn
        </button>
    </div>

    <!-- MODAL ĐĂNG NHẬP PHỦ KÍN 100% -->
    <div id="authOverlay">
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
    
    <!-- MODAL TẠO MẬT KHẨU -->
    <div id="setPwdModal" style="display:none; position:fixed; inset:0; z-index:1000000; background:rgba(15, 23, 42, 0.95); backdrop-filter:blur(8px); align-items:center; justify-content:center; padding:1rem;">
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
    
    <!-- MODAL GIA HẠN / NẠP TIỀN -->
    <div id="renewalModal">
        <div class="renewal-box">
            <button class="auth-close" onclick="triggerSignOut()" title="Đăng xuất" style="position:absolute;top:1rem;right:1rem;background:none;border:none;color:#94a3b8;font-size:1.25rem;cursor:pointer;">✕</button>
            <div class="renewal-icon"><i class="fa-solid fa-clock"></i></div>
            <h2 class="auth-title" style="color:#10b981;">Gia hạn tài khoản</h2>
            <p class="auth-sub">Chọn gói gia hạn để tiếp tục sử dụng hệ thống.</p>
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
                <button class="auth-btn outline" onclick="triggerSignOut()">Đăng xuất</button>
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
        
        function waitAuth(cb) {{
            var t = setInterval(function() {{
                if (typeof firebase !== 'undefined' && typeof window.auth !== 'undefined' && typeof window.db !== 'undefined') {{
                    clearInterval(t); cb();
                }}
            }}, 200);
        }}

        // HÀM ĐĂNG XUẤT AN TOÀN - KHÓA CỨNG TRANG NGAY LẬP TỨC
        window.triggerSignOut = async function() {{
            var authOverlay = document.getElementById('authOverlay');
            if (authOverlay) authOverlay.classList.remove('hidden');
            document.body.classList.add('auth-locked');

            var renewal = document.getElementById('renewalModal');
            if (renewal) renewal.classList.remove('show');
            
            var adminModal = document.getElementById('admin-modal');
            if (adminModal) adminModal.classList.add('hidden');

            var expireBadge = document.getElementById('userExpireBadge');
            if (expireBadge) expireBadge.style.display = 'none';

            var adminList = document.getElementById('admin-users-list');
            if (adminList) adminList.innerHTML = `<tr><td colspan="3" class="p-4 text-center text-slate-500">Chưa đăng nhập...</td></tr>`;

            try {{
                if (window.auth) {{
                    await window.auth.signOut();
                }}
            }} catch(e) {{
                console.warn('SignOut error:', e);
            }}
        }};

        waitAuth(function() {{
            var auth = window.auth;
            var db = window.db;

            auth.onAuthStateChanged(async function(user) {{
                var authOverlay = document.getElementById('authOverlay');
                var adminModal = document.getElementById('admin-modal');
                var expireBadge = document.getElementById('userExpireBadge');
                
                if (user) {{
                    if (authOverlay) authOverlay.classList.add('hidden');
                    document.body.classList.remove('auth-locked');
                    if (expireBadge) expireBadge.style.display = 'inline-flex';
                    
                    await checkUserPermission(user);
                    if (typeof window.onAuthReady === 'function') {{
                        try {{ await window.onAuthReady(user); }} catch(e) {{ console.warn(e); }}
                    }}
                }} else {{
                    if (authOverlay) authOverlay.classList.remove('hidden');
                    document.body.classList.add('auth-locked');
                    if (expireBadge) expireBadge.style.display = 'none';
                    if (adminModal) adminModal.classList.add('hidden');
                    
                    var adminList = document.getElementById('admin-users-list');
                    if (adminList) adminList.innerHTML = `<tr><td colspan="3" class="p-4 text-center text-slate-500">Chưa đăng nhập...</td></tr>`;
                    var renewal = document.getElementById('renewalModal');
                    if (renewal) renewal.classList.remove('show');
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
                
                msgBox.className = 'auth-msg';
                msgBox.innerHTML = '';

                if (!email || !pwd) return showMsg('loginMsg', 'Vui lòng nhập đủ email và mật khẩu.', 'error');
                
                btn.disabled = true; 
                btnSpan.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang kết nối...';
                
                try {{
                    await auth.signInWithEmailAndPassword(email, pwd);
                }} catch(e) {{
                    var errMsg = e.message;
                    if (e.code === 'auth/user-not-found') errMsg = 'Tài khoản chưa tồn tại. Vui lòng đăng nhập bằng Google hoặc bấm "Tạo tài khoản".';
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
                sessionStorage.getItem('asked_pwd_' + user.email, '1');
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
                        updateExpireUI(expireDate);
                    }} else {{
                        var data = doc.data();
                        if (data.expiresAt) {{
                            var exp = new Date(data.expiresAt);
                            updateExpireUI(exp);
                            
                            if (data.role !== 'admin' && new Date() > exp) {{
                                document.getElementById('renewalModal').classList.add('show');
                                var authOverlay = document.getElementById('authOverlay');
                                if (authOverlay) authOverlay.classList.add('hidden');
                            }} else {{
                                var renewal = document.getElementById('renewalModal');
                                if (renewal) renewal.classList.remove('show');
                            }}
                        }}
                    }}
                }} catch(e) {{ console.warn('Lỗi check quyền:', e); }}
            }}

            function updateExpireUI(expDate) {{
                var txt = document.getElementById('expireDateText');
                if (txt) {{
                    txt.innerText = 'Hạn dùng: ' + expDate.toLocaleDateString('vi-VN');
                }}
            }}

            window.openUserRenewalModal = function() {{
                var renewal = document.getElementById('renewalModal');
                if (renewal) {{
                    renewal.classList.add('show');
                    selectedPkgId = null;
                    document.querySelectorAll('.package-item').forEach(function(el) {{ el.classList.remove('active'); }});
                    var qrWrap = document.getElementById('qrCodeWrap');
                    if (qrWrap) qrWrap.style.display = 'none';
                    var btnPay = document.getElementById('btnConfirmPay');
                    if (btnPay) btnPay.style.display = 'none';
                }}
            }};

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
