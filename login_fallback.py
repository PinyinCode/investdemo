# -*- coding: utf-8 -*-
"""Module đặt mật khẩu lần đầu + form Email/Password nhúng thẳng vào #loginModal.
Tự động thêm @gmail.com nếu user chỉ nhập username, cảnh báo nếu domain khác."""


def build_login_fallback_css():
    return r"""
/* ============ FORM EMAIL NHÚNG TRONG #loginModal ============ */
.elf-inline-form{margin-top:1rem;padding-top:1rem;border-top:1px solid #e2e8f0}
[data-theme="dark"] .elf-inline-form{border-color:#334155}

.elf-divider{display:flex;align-items:center;gap:.5rem;margin-bottom:.85rem;color:#94a3b8;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.elf-divider::before,.elf-divider::after{content:"";flex:1;height:1px;background:#e2e8f0}
[data-theme="dark"] .elf-divider::before,[data-theme="dark"] .elf-divider::after{background:#334155}

.elf-tabs{display:flex;gap:.25rem;background:#f1f5f9;border-radius:10px;padding:.25rem;margin-bottom:1rem}
[data-theme="dark"] .elf-tabs{background:#0f172a}
.elf-tab{flex:1;padding:.5rem;border:none;background:transparent;color:#64748b;font-weight:700;font-size:.82rem;border-radius:8px;cursor:pointer;transition:.15s;font-family:inherit}
.elf-tab.active{background:#fff;color:#4f46e5;box-shadow:0 2px 6px rgba(0,0,0,.08)}
[data-theme="dark"] .elf-tab.active{background:#1e293b;color:#a78bfa}

.elf-field{margin-bottom:.7rem;text-align:left}
.elf-field label{display:block;font-size:.72rem;font-weight:700;color:#475569;margin-bottom:.35rem;text-transform:uppercase;letter-spacing:.3px}
[data-theme="dark"] .elf-field label{color:#cbd5e1}
.elf-field input{width:100%;padding:.65rem .85rem;border-radius:10px;border:1.5px solid #e2e8f0;background:#fff;color:#0f172a;font-size:.88rem;font-family:inherit;outline:none;transition:.15s;box-sizing:border-box}
.elf-field input:focus{border-color:#4f46e5;box-shadow:0 0 0 3px rgba(79,70,229,.15)}
[data-theme="dark"] .elf-field input{background:#0f172a;border-color:#475569;color:#f1f5f9}
[data-theme="dark"] .elf-field input:focus{border-color:#818cf8;box-shadow:0 0 0 3px rgba(129,140,248,.2)}

/* Email preview + trạng thái lỗi */
.elf-email-preview{font-size:.72rem;margin-top:.35rem;line-height:1.4;display:none}
.elf-email-preview.ok{color:#16a34a}
.elf-email-preview.error{color:#dc2626}
.elf-email-preview b{font-weight:700}
[data-theme="dark"] .elf-email-preview.ok{color:#4ade80}
[data-theme="dark"] .elf-email-preview.error{color:#fca5a5}
.elf-field input.elf-input-error{border-color:#dc2626 !important;box-shadow:0 0 0 3px rgba(220,38,38,.15) !important}
[data-theme="dark"] .elf-field input.elf-input-error{border-color:#f87171 !important}

.elf-pwd-wrap{position:relative}
.elf-pwd-wrap input{padding-right:2.6rem}
.elf-pwd-toggle{position:absolute;right:.55rem;top:50%;transform:translateY(-50%);width:30px;height:30px;border:none;background:transparent;color:#94a3b8;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:.85rem;border-radius:8px;transition:.15s}
.elf-pwd-toggle:hover{background:#f1f5f9;color:#4f46e5}
[data-theme="dark"] .elf-pwd-toggle:hover{background:#334155;color:#a78bfa}

.elf-btn-submit{display:flex;align-items:center;justify-content:center;gap:.5rem;width:100%;padding:.75rem 1rem;border-radius:12px;border:none;background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;font-size:.88rem;font-weight:800;font-family:inherit;cursor:pointer;transition:.2s;box-shadow:0 4px 14px rgba(124,58,237,.3);margin-top:.25rem}
.elf-btn-submit:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 8px 22px rgba(124,58,237,.45)}
.elf-btn-submit:active:not(:disabled){transform:translateY(0) scale(.98)}
.elf-btn-submit:disabled{opacity:.6;cursor:not-allowed;transform:none;box-shadow:none}

.elf-inline-extra{display:flex;justify-content:space-between;align-items:center;margin-top:.6rem;font-size:.75rem;flex-wrap:wrap;gap:.35rem}
.elf-link{color:#4f46e5;font-weight:700;cursor:pointer;background:none;border:none;font-family:inherit;padding:.2rem .35rem;border-radius:6px;transition:.15s;font-size:inherit}
.elf-link:hover{background:#ede9fe;text-decoration:underline}
[data-theme="dark"] .elf-link{color:#93c5fd}
[data-theme="dark"] .elf-link:hover{background:rgba(147,197,253,.15)}

.elf-inline-msg{padding:.65rem .8rem;border-radius:10px;font-size:.8rem;margin-top:.75rem;display:none;text-align:left;line-height:1.45}
.elf-inline-msg.show{display:block}
.elf-inline-msg.error{background:#fee2e2;color:#dc2626}
.elf-inline-msg.success{background:#dcfce7;color:#15803d}
.elf-inline-msg.info{background:#dbeafe;color:#1e40af}
[data-theme="dark"] .elf-inline-msg.error{background:rgba(220,38,38,.2);color:#fca5a5}
[data-theme="dark"] .elf-inline-msg.success{background:rgba(22,163,74,.2);color:#4ade80}
[data-theme="dark"] .elf-inline-msg.info{background:rgba(59,130,246,.2);color:#93c5fd}

.elf-form-hidden{display:none !important}

.elf-spinner{display:inline-block;width:15px;height:15px;border:2px solid rgba(255,255,255,.35);border-top-color:#fff;border-radius:50%;animation:elfSpin .7s linear infinite}
@keyframes elfSpin{to{transform:rotate(360deg)}}

/* ============ MODAL ĐẶT MẬT KHẨU ============ */
.elf-modal{position:fixed;inset:0;background:rgba(15,23,42,.85);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);z-index:3100;display:none;align-items:center;justify-content:center;padding:1.25rem;overflow-y:auto;animation:elfFadeIn .2s ease}
.elf-modal.show{display:flex}
@keyframes elfFadeIn{from{opacity:0}to{opacity:1}}
.elf-box{background:#fff;border-radius:20px;padding:2rem 1.75rem;max-width:440px;width:100%;max-height:calc(100vh - 2.5rem);overflow-y:auto;box-shadow:0 24px 70px rgba(0,0,0,.35);text-align:center;position:relative;animation:elfSlideUp .32s cubic-bezier(.34,1.56,.64,1)}
[data-theme="dark"] .elf-box{background:#1e293b;color:#f1f5f9}
@keyframes elfSlideUp{from{transform:translateY(30px) scale(.95);opacity:0}to{transform:translateY(0) scale(1);opacity:1}}
.elf-close{position:absolute;top:12px;right:12px;width:34px;height:34px;border-radius:50%;border:none;background:#f1f5f9;color:#475569;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;transition:.15s}
.elf-close:hover{background:#fee2e2;color:#dc2626}
[data-theme="dark"] .elf-close{background:#334155;color:#cbd5e1}
[data-theme="dark"] .elf-close:hover{background:#7f1d1d;color:#fecaca}
.elf-logo{width:64px;height:64px;background:linear-gradient(135deg,#4f46e5,#7c3aed);border-radius:18px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.75rem;margin:0 auto 1.25rem;box-shadow:0 8px 20px rgba(124,58,237,.35)}
.elf-title{font-size:1.3rem;color:#0f172a;margin-bottom:.4rem;font-weight:800}
[data-theme="dark"] .elf-title{color:#f1f5f9}
.elf-subtitle{color:#64748b;font-size:.85rem;margin-bottom:1.5rem;line-height:1.55}
[data-theme="dark"] .elf-subtitle{color:#94a3b8}
.elf-account-info{display:flex;align-items:center;gap:.75rem;padding:.85rem 1rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;margin-bottom:1.25rem;text-align:left}
[data-theme="dark"] .elf-account-info{background:#0f172a;border-color:#334155}
.elf-account-avatar{width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#4f46e5);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:1.15rem;flex-shrink:0;overflow:hidden}
.elf-account-avatar img{width:100%;height:100%;object-fit:cover}
.elf-account-info .elf-acc-text{flex:1;min-width:0}
.elf-account-info .elf-acc-name{font-weight:700;font-size:.9rem;color:#0f172a;margin-bottom:.15rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.elf-account-info .elf-acc-email{font-size:.75rem;color:#64748b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
[data-theme="dark"] .elf-account-info .elf-acc-name{color:#f1f5f9}
[data-theme="dark"] .elf-account-info .elf-acc-email{color:#94a3b8}
.elf-tip-banner{display:flex;align-items:flex-start;gap:.6rem;padding:.7rem .85rem;background:linear-gradient(135deg,rgba(79,70,229,.08),rgba(124,58,237,.06));border:1px solid rgba(124,58,237,.25);border-radius:12px;margin-bottom:1.25rem;font-size:.78rem;color:#5b21b6;line-height:1.5;text-align:left}
[data-theme="dark"] .elf-tip-banner{background:linear-gradient(135deg,rgba(124,58,237,.15),rgba(79,70,229,.1));border-color:rgba(165,180,252,.3);color:#c4b5fd}
.elf-tip-banner i{color:#7c3aed;margin-top:.15rem;flex-shrink:0;font-size:1rem}
.elf-tip-banner b{color:#4f46e5}
[data-theme="dark"] .elf-tip-banner b{color:#a78bfa}
.elf-footer{margin-top:1.25rem;padding-top:1rem;border-top:1px solid #e2e8f0;font-size:.72rem;color:#94a3b8;line-height:1.55;text-align:center}
.elf-footer b{color:#4f46e5}
[data-theme="dark"] .elf-footer{border-color:#475569;color:#94a3b8}
[data-theme="dark"] .elf-footer b{color:#a78bfa}
.elf-strength{margin-top:.35rem;display:flex;gap:.25rem}
.elf-strength-bar{flex:1;height:4px;border-radius:2px;background:#e2e8f0;transition:.25s}
.elf-strength-bar.weak{background:#dc2626}
.elf-strength-bar.medium{background:#f59e0b}
.elf-strength-bar.strong{background:#16a34a}
.elf-btn{display:flex;align-items:center;justify-content:center;gap:.5rem;width:100%;padding:.85rem 1.25rem;border-radius:12px;border:none;background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;font-size:.92rem;font-weight:800;font-family:inherit;cursor:pointer;transition:.2s;box-shadow:0 4px 14px rgba(124,58,237,.35);letter-spacing:.2px;margin-top:.25rem}
.elf-btn:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 8px 22px rgba(124,58,237,.5)}
.elf-btn:active:not(:disabled){transform:translateY(0) scale(.98)}
.elf-btn:disabled{opacity:.6;cursor:not-allowed;transform:none;box-shadow:none}
.elf-btn.ghost{background:transparent;color:#64748b;border:none;box-shadow:none;font-weight:600;font-size:.82rem}
.elf-btn.ghost:hover:not(:disabled){color:#4f46e5;text-decoration:underline}
@media(max-width:500px){
.elf-box{padding:1.5rem 1.25rem;border-radius:16px}
.elf-logo{width:56px;height:56px;font-size:1.5rem}
.elf-title{font-size:1.15rem}
.elf-subtitle{font-size:.8rem}
}
"""


def build_login_fallback_html():
    """Chỉ còn modal đặt mật khẩu. Form email được JS inject vào #loginModal."""
    return r"""
<div class="elf-modal" id="elfSetPwdModal">
    <div class="elf-box">
        <button class="elf-close" id="elfSetPwdClose" type="button" aria-label="Đóng sau">
            <i class="fas fa-times"></i>
        </button>
        <div class="elf-logo"><i class="fas fa-shield-halved"></i></div>
        <div class="elf-title">Đặt mật khẩu đăng nhập</div>
        <div class="elf-subtitle">Đặt mật khẩu để lần sau có thể đăng nhập bằng email ngay cả khi Google gặp sự cố.</div>
        <div class="elf-account-info">
            <div class="elf-account-avatar" id="elfSetAvatar">?</div>
            <div class="elf-acc-text">
                <div class="elf-acc-name" id="elfSetName">-</div>
                <div class="elf-acc-email" id="elfSetEmail">-</div>
            </div>
        </div>
        <div class="elf-tip-banner">
            <i class="fas fa-lightbulb"></i>
            <div><b>Gợi ý:</b> Đặt mật khẩu dễ nhớ (tối thiểu 6 ký tự) để đăng nhập nhanh hơn. Bạn vẫn có thể dùng Google như bình thường.</div>
        </div>
        <form id="elfSetPwdForm" autocomplete="on" novalidate>
            <div class="elf-field">
                <label>Mật khẩu mới</label>
                <div class="elf-pwd-wrap">
                    <input type="password" id="elfSetPwd1" placeholder="Tối thiểu 6 ký tự" autocomplete="new-password" required minlength="6">
                    <button type="button" class="elf-pwd-toggle" data-elf-pwd="elfSetPwd1" aria-label="Hiện/ẩn mật khẩu"><i class="fas fa-eye"></i></button>
                </div>
                <div class="elf-strength" id="elfSetStrength">
                    <div class="elf-strength-bar"></div>
                    <div class="elf-strength-bar"></div>
                    <div class="elf-strength-bar"></div>
                </div>
            </div>
            <div class="elf-field">
                <label>Nhập lại mật khẩu</label>
                <div class="elf-pwd-wrap">
                    <input type="password" id="elfSetPwd2" placeholder="Nhập lại mật khẩu" autocomplete="new-password" required minlength="6">
                    <button type="button" class="elf-pwd-toggle" data-elf-pwd="elfSetPwd2" aria-label="Hiện/ẩn mật khẩu"><i class="fas fa-eye"></i></button>
                </div>
            </div>
            <button type="submit" class="elf-btn" id="elfSetPwdSubmit">
                <i class="fas fa-check"></i> Lưu mật khẩu
            </button>
            <button type="button" class="elf-btn ghost" id="elfSetPwdSkip" style="margin-top:.5rem;">Để sau</button>
        </form>
        <div class="elf-msg" id="elfSetMsg" style="padding:.75rem .9rem;border-radius:10px;font-size:.82rem;margin-top:1rem;display:none;text-align:left;line-height:1.45"></div>
        <div class="elf-footer">
            <i class="fas fa-lock" style="color:#4f46e5"></i>
            Mật khẩu được gắn vào <b>cùng tài khoản Google</b> của bạn — không tạo tài khoản mới.
        </div>
    </div>
</div>
"""


def build_login_fallback_js():
    return r"""
(function() {
    'use strict';

    var PWD_ASKED_KEY = 'elf_pwd_asked_';
    var ALLOWED_DOMAINS = ['gmail.com', 'googlemail.com'];

    function waitAuth(cb) {
        var tries = 0;
        var t = setInterval(function() {
            tries++;
            try {
                if (typeof auth !== 'undefined' && auth && typeof firebase !== 'undefined') {
                    clearInterval(t);
                    cb();
                    return;
                }
            } catch(e) {}
            if (tries > 40) clearInterval(t);
        }, 250);
    }

    function showMsg(elId, msg, type) {
        var el = document.getElementById(elId);
        if (!el) return;
        el.className = 'elf-inline-msg show' + (type ? ' ' + type : '');
        el.innerHTML = msg;
    }

    function clearMsg(elId) {
        var el = document.getElementById(elId);
        if (!el) return;
        el.className = 'elf-inline-msg';
        el.innerHTML = '';
    }

    /* ============ XỬ LÝ EMAIL GMAIL ============ */
    function normalizeGmailEmail(rawInput) {
        /* Trả về: { email: 'xxx@gmail.com' | null, error: 'msg' | null } */
        var v = (rawInput || '').trim().toLowerCase().replace(/\s+/g, '');
        if (!v) return { email: null, error: 'Vui lòng nhập email.' };

        if (v.indexOf('@') !== -1) {
            var parts = v.split('@');
            if (parts.length > 2) {
                return { email: null, error: 'Email không được có nhiều hơn 1 ký tự @.' };
            }

            var localPart = parts[0];
            var domain = parts[1];

            if (!localPart) {
                return { email: null, error: 'Thiếu phần tên email (trước dấu @).' };
            }

            var normDomain = domain;
            if (normDomain === 'gmail' || normDomain === 'googlemail') {
                normDomain = normDomain + '.com';
            }

            if (ALLOWED_DOMAINS.indexOf(normDomain) === -1) {
                return {
                    email: null,
                    error: 'Vui lòng dùng địa chỉ <b>@gmail.com</b>. Bạn đã nhập <b>@' + domain + '</b>.'
                };
            }

            if (!/^[a-z0-9.]+$/.test(localPart)) {
                return { email: null, error: 'Tên email chỉ được chứa chữ, số và dấu chấm.' };
            }
            if (localPart.indexOf('..') !== -1) {
                return { email: null, error: 'Email không được có 2 dấu chấm liền nhau.' };
            }
            if (localPart[0] === '.' || localPart[localPart.length - 1] === '.') {
                return { email: null, error: 'Email không được bắt đầu/kết thúc bằng dấu chấm.' };
            }

            return { email: localPart + '@' + normDomain, error: null };
        }

        /* Không có @ → tự thêm @gmail.com */
        if (!/^[a-z0-9.]+$/.test(v)) {
            return { email: null, error: 'Tên email chỉ được chứa chữ, số và dấu chấm.' };
        }
        if (v.indexOf('..') !== -1) {
            return { email: null, error: 'Email không được có 2 dấu chấm liền nhau.' };
        }
        if (v[0] === '.' || v[v.length - 1] === '.') {
            return { email: null, error: 'Email không được bắt đầu/kết thúc bằng dấu chấm.' };
        }

        return { email: v + '@gmail.com', error: null };
    }

    function updateEmailPreview(inputId, previewId) {
        var inp = document.getElementById(inputId);
        var prev = document.getElementById(previewId);
        if (!inp || !prev) return;

        var raw = inp.value;
        if (!raw.trim()) {
            prev.style.display = 'none';
            prev.innerHTML = '';
            inp.classList.remove('elf-input-error');
            return;
        }

        var res = normalizeGmailEmail(raw);

        if (res.error) {
            prev.style.display = 'block';
            prev.className = 'elf-email-preview error';
            prev.innerHTML = '<i class="fas fa-exclamation-triangle"></i> ' + res.error;
            inp.classList.add('elf-input-error');
        } else {
            prev.style.display = 'block';
            prev.className = 'elf-email-preview ok';
            if (res.email !== raw.trim().toLowerCase()) {
                prev.innerHTML = '<i class="fas fa-check-circle"></i> Sẽ dùng: <b>' + res.email + '</b>';
            } else {
                prev.innerHTML = '<i class="fas fa-check-circle"></i> Email hợp lệ';
            }
            inp.classList.remove('elf-input-error');
        }
    }

    /* ============ MODAL ĐẶT MẬT KHẨU ============ */
    function openSetPwdModal() {
        var m = document.getElementById('elfSetPwdModal');
        if (!m) return;
        m.classList.add('show');
        clearMsg('elfSetMsg');
        try {
            var u = auth.currentUser;
            if (u) {
                var av = document.getElementById('elfSetAvatar');
                var nm = document.getElementById('elfSetName');
                var em = document.getElementById('elfSetEmail');
                if (em) em.textContent = u.email || '';
                var name = u.displayName || (u.email || '').split('@')[0];
                if (nm) nm.textContent = name;
                if (av) {
                    if (u.photoURL) av.innerHTML = '<img src="' + u.photoURL + '" alt="">';
                    else av.textContent = (name.charAt(0) || '?').toUpperCase();
                }
            }
        } catch(e) {}
        setTimeout(function() {
            var inp = document.getElementById('elfSetPwd1');
            if (inp) inp.focus();
        }, 150);
    }

    function closeSetPwdModal() {
        var m = document.getElementById('elfSetPwdModal');
        if (!m) return;
        m.classList.remove('show');
        clearMsg('elfSetMsg');
    }

    function userHasPassword(user) {
        if (!user) return false;
        try {
            var providers = user.providerData || [];
            for (var i = 0; i < providers.length; i++) {
                if (providers[i].providerId === 'password') return true;
            }
        } catch(e) {}
        return false;
    }

    function userHasGoogle(user) {
        if (!user) return false;
        try {
            var providers = user.providerData || [];
            for (var i = 0; i < providers.length; i++) {
                if (providers[i].providerId === 'google.com') return true;
            }
        } catch(e) {}
        return false;
    }

    function checkAndAskSetPassword(user) {
        if (!user || !user.email) return;
        if (!userHasGoogle(user)) return;
        if (userHasPassword(user)) return;

        var email = user.email.toLowerCase();
        try {
            if (sessionStorage.getItem(PWD_ASKED_KEY + email) === '1') return;
        } catch(e) {}

        var busyModals = [
            'adminModal','importModal','editExpiryModal','changeNameModal',
            'renewalModal','permissionModal','onboardingModal','voiceModal',
            'writerModal','practiceFullModal','chatModal'
        ];
        for (var i = 0; i < busyModals.length; i++) {
            var m = document.getElementById(busyModals[i]);
            if (m && m.classList.contains('show')) {
                (function(mod) {
                    var timer = setInterval(function() {
                        if (!mod.classList.contains('show')) {
                            clearInterval(timer);
                            checkAndAskSetPassword(user);
                        }
                    }, 500);
                })(m);
                return;
            }
        }

        try { sessionStorage.setItem(PWD_ASKED_KEY + email, '1'); } catch(e) {}
        setTimeout(openSetPwdModal, 1500);
    }

    async function handleSetPassword(e) {
        if (e) e.preventDefault();
        var p1 = document.getElementById('elfSetPwd1').value || '';
        var p2 = document.getElementById('elfSetPwd2').value || '';
        var btn = document.getElementById('elfSetPwdSubmit');

        if (p1.length < 6) { showSetPwdMsg('Mật khẩu phải từ 6 ký tự trở lên.', 'error'); return; }
        if (p1 !== p2) { showSetPwdMsg('Mật khẩu nhập lại không khớp.', 'error'); return; }

        var user = auth.currentUser;
        if (!user || !user.email) {
            showSetPwdMsg('Không tìm thấy thông tin tài khoản. Vui lòng thử lại.', 'error');
            return;
        }

        var orig = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="elf-spinner"></span> Đang lưu...';

        try {
            var credential = firebase.auth.EmailAuthProvider.credential(user.email, p1);
            await user.linkWithCredential(credential);
            try { sessionStorage.removeItem(PWD_ASKED_KEY + user.email.toLowerCase()); } catch(e) {}

            showSetPwdMsg('✅ Đặt mật khẩu thành công!<br>Lần sau bạn có thể đăng nhập bằng Email.', 'success');
            setTimeout(function() { closeSetPwdModal(); }, 1500);
        } catch (err) {
            console.error('[ELF SetPwd]', err);
            var msg = 'Lỗi: ' + (err.code || err.message);
            if (err.code === 'auth/provider-already-linked') msg = 'Tài khoản này đã có mật khẩu.';
            else if (err.code === 'auth/email-already-in-use') msg = 'Email này đã có mật khẩu riêng. Dùng <b>Quên mật khẩu</b>.';
            else if (err.code === 'auth/weak-password') msg = 'Mật khẩu quá yếu.';
            else if (err.code === 'auth/requires-recent-login') msg = 'Phiên đăng nhập đã cũ. Đăng xuất rồi đăng nhập lại Google.';
            else if (err.code === 'auth/credential-already-in-use') msg = 'Email đã liên kết tài khoản khác.';
            else if (err.code === 'auth/operation-not-allowed') msg = '⚠️ Chưa bật <b>Email/Password</b> trên Firebase Console.';
            showSetPwdMsg(msg, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = orig;
        }
    }

    function showSetPwdMsg(msg, type) {
        var el = document.getElementById('elfSetMsg');
        if (!el) return;
        el.style.display = 'block';
        el.style.background = type === 'error' ? '#fee2e2' : '#dcfce7';
        el.style.color = type === 'error' ? '#dc2626' : '#15803d';
        el.innerHTML = msg;
    }

    function updateStrength(pwd) {
        var bars = document.querySelectorAll('#elfSetStrength .elf-strength-bar');
        if (!bars.length) return;
        var score = 0;
        if (pwd.length >= 6) score++;
        if (pwd.length >= 10) score++;
        if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score++;
        if (/[0-9]/.test(pwd)) score++;
        if (/[^A-Za-z0-9]/.test(pwd)) score++;

        var level = score >= 4 ? 3 : (score >= 3 ? 2 : (score >= 2 ? 1 : 0));
        bars.forEach(function(b, i) {
            b.className = 'elf-strength-bar';
            if (i < level) {
                b.classList.add(level === 1 ? 'weak' : level === 2 ? 'medium' : 'strong');
            }
        });
    }

    /* ============ FORM EMAIL NHÚNG TRONG #loginModal ============ */
    function buildInlineFormHTML() {
        return '' +
        '<div class="elf-inline-form" id="elfInlineForm">' +
            '<div class="elf-divider"><span>Hoặc</span></div>' +
            '<div class="elf-tabs">' +
                '<button type="button" class="elf-tab active" data-elf-tab="login"><i class="fas fa-sign-in-alt"></i> Đăng nhập</button>' +
                '<button type="button" class="elf-tab" data-elf-tab="register"><i class="fas fa-user-plus"></i> Đăng ký</button>' +
            '</div>' +

            /* Form đăng nhập */
            '<form id="elfInlineLoginForm" class="elf-inline-form-body" autocomplete="on" novalidate>' +
                '<div class="elf-field">' +
                    '<label>Email</label>' +
                    '<input type="text" id="elfLoginEmail" placeholder="Nhập Gmail ( @gmail.com)" autocomplete="email" required inputmode="email">' +
                    '<div class="elf-email-preview" id="elfLoginEmailPreview"></div>' +
                '</div>' +
                '<div class="elf-field">' +
                    '<label>Mật khẩu</label>' +
                    '<div class="elf-pwd-wrap">' +
                        '<input type="password" id="elfLoginPwd" placeholder="Tối thiểu 6 ký tự" autocomplete="current-password" required minlength="6">' +
                        '<button type="button" class="elf-pwd-toggle" data-elf-pwd="elfLoginPwd" aria-label="Hiện/ẩn mật khẩu"><i class="fas fa-eye"></i></button>' +
                    '</div>' +
                '</div>' +
                '<button type="submit" class="elf-btn-submit" id="elfLoginSubmit">' +
                    '<i class="fas fa-sign-in-alt"></i> Đăng nhập' +
                '</button>' +
                '<div class="elf-inline-extra">' +
                    '<button type="button" class="elf-link" id="elfForgotBtn"><i class="fas fa-key"></i> Quên mật khẩu?</button>' +
                '</div>' +
            '</form>' +

            /* Form đăng ký */
            '<form id="elfInlineRegisterForm" class="elf-inline-form-body elf-form-hidden" autocomplete="on" novalidate>' +
                '<div class="elf-field">' +
                    '<label>Email</label>' +
                    '<input type="text" id="elfRegEmail" placeholder="Nhập tên email (tự thêm @gmail.com)" autocomplete="email" required inputmode="email">' +
                    '<div class="elf-email-preview" id="elfRegEmailPreview"></div>' +
                '</div>' +
                '<div class="elf-field">' +
                    '<label>Họ tên (tùy chọn)</label>' +
                    '<input type="text" id="elfRegName" placeholder="Nguyễn Văn A" autocomplete="name" maxlength="50">' +
                '</div>' +
                '<div class="elf-field">' +
                    '<label>Mật khẩu</label>' +
                    '<div class="elf-pwd-wrap">' +
                        '<input type="password" id="elfRegPwd" placeholder="Tối thiểu 6 ký tự" autocomplete="new-password" required minlength="6">' +
                        '<button type="button" class="elf-pwd-toggle" data-elf-pwd="elfRegPwd" aria-label="Hiện/ẩn mật khẩu"><i class="fas fa-eye"></i></button>' +
                    '</div>' +
                '</div>' +
                '<div class="elf-field">' +
                    '<label>Nhập lại mật khẩu</label>' +
                    '<div class="elf-pwd-wrap">' +
                        '<input type="password" id="elfRegPwd2" placeholder="Nhập lại mật khẩu" autocomplete="new-password" required minlength="6">' +
                        '<button type="button" class="elf-pwd-toggle" data-elf-pwd="elfRegPwd2" aria-label="Hiện/ẩn mật khẩu"><i class="fas fa-eye"></i></button>' +
                    '</div>' +
                '</div>' +
                '<button type="submit" class="elf-btn-submit" id="elfRegisterSubmit">' +
                    '<i class="fas fa-user-plus"></i> Tạo tài khoản' +
                '</button>' +
            '</form>' +

            '<div class="elf-inline-msg" id="elfMsg"></div>' +
        '</div>';
    }

    function injectInlineForm() {
        var loginBox = document.querySelector('#loginModal .login-box');
        if (!loginBox) return false;
        if (loginBox.querySelector('#elfInlineForm')) return true;

        var footer = loginBox.querySelector('.login-footer');
        var wrap = document.createElement('div');
        wrap.innerHTML = buildInlineFormHTML();
        var formEl = wrap.firstChild;

        if (footer && footer.parentNode === loginBox) {
            loginBox.insertBefore(formEl, footer);
        } else {
            loginBox.appendChild(formEl);
        }

        bindInlineEvents();
        return true;
    }

    function bindInlineEvents() {
        /* Tabs */
        document.querySelectorAll('.elf-tab').forEach(function(tab) {
            if (tab.__elfBound) return;
            tab.__elfBound = true;
            tab.addEventListener('click', function() {
                var target = this.dataset.elfTab;
                document.querySelectorAll('.elf-tab').forEach(function(t) {
                    t.classList.toggle('active', t === tab);
                });
                var lf = document.getElementById('elfInlineLoginForm');
                var rf = document.getElementById('elfInlineRegisterForm');
                if (target === 'login') {
                    if (lf) lf.classList.remove('elf-form-hidden');
                    if (rf) rf.classList.add('elf-form-hidden');
                } else {
                    if (lf) lf.classList.add('elf-form-hidden');
                    if (rf) rf.classList.remove('elf-form-hidden');
                    setTimeout(function() {
                        var i = document.getElementById('elfRegEmail');
                        if (i) i.focus();
                    }, 100);
                }
                clearMsg('elfMsg');
            });
        });

        /* Email realtime preview + auto-fill khi blur */
        ['elfLoginEmail', 'elfRegEmail'].forEach(function(id) {
            var inp = document.getElementById(id);
            if (!inp || inp.__elfEmailBound) return;
            inp.__elfEmailBound = true;

            inp.addEventListener('input', function() {
                updateEmailPreview(id, id + 'Preview');
                clearMsg('elfMsg');
            });

            inp.addEventListener('blur', function() {
                var res = normalizeGmailEmail(this.value);
                if (!res.error && res.email !== this.value.trim().toLowerCase()) {
                    this.value = res.email;
                    updateEmailPreview(id, id + 'Preview');
                }
            });
        });

        /* Pwd toggles */
        document.querySelectorAll('.elf-pwd-toggle').forEach(function(btn) {
            if (btn.__elfBound) return;
            btn.__elfBound = true;
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                var inp = document.getElementById(this.dataset.elfPwd);
                if (!inp) return;
                var isPwd = inp.type === 'password';
                inp.type = isPwd ? 'text' : 'password';
                var icon = this.querySelector('i');
                if (icon) icon.className = isPwd ? 'fas fa-eye-slash' : 'fas fa-eye';
            });
        });

        /* Login form submit */
        var lf = document.getElementById('elfInlineLoginForm');
        if (lf && !lf.__elfBound) {
            lf.__elfBound = true;
            lf.addEventListener('submit', doEmailLogin);
        }

        /* Register form submit */
        var rf = document.getElementById('elfInlineRegisterForm');
        if (rf && !rf.__elfBound) {
            rf.__elfBound = true;
            rf.addEventListener('submit', doEmailRegister);
        }

        /* Forgot */
        var fb = document.getElementById('elfForgotBtn');
        if (fb && !fb.__elfBound) {
            fb.__elfBound = true;
            fb.addEventListener('click', doForgot);
        }
    }

    async function doEmailLogin(e) {
        if (e) e.preventDefault();
        var rawEmail = document.getElementById('elfLoginEmail').value || '';
        var pwd = document.getElementById('elfLoginPwd').value || '';
        var btn = document.getElementById('elfLoginSubmit');

        var res = normalizeGmailEmail(rawEmail);
        if (res.error) {
            showMsg('elfMsg', res.error, 'error');
            return;
        }
        var email = res.email;

        /* Cập nhật lại input cho user thấy email chuẩn hoá */
        document.getElementById('elfLoginEmail').value = email;
        updateEmailPreview('elfLoginEmail', 'elfLoginEmailPreview');

        if (!pwd) { showMsg('elfMsg', 'Vui lòng nhập mật khẩu.', 'error'); return; }

        var orig = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="elf-spinner"></span> Đang đăng nhập...';

        try {
            await auth.signInWithEmailAndPassword(email, pwd);
            showMsg('elfMsg', '✅ Đăng nhập thành công!', 'success');
            setTimeout(function() {
                try {
                    if (typeof hideLoginModal === 'function') hideLoginModal();
                    else {
                        var lm = document.getElementById('loginModal');
                        if (lm) lm.classList.remove('show');
                    }
                } catch(_e) {}
                clearMsg('elfMsg');
            }, 600);
        } catch (err) {
            console.error('[ELF Login]', err);
            var msg = 'Lỗi: ' + (err.code || err.message);
            if (err.code === 'auth/user-not-found') msg = 'Không tìm thấy tài khoản. Bạn có muốn <b>Đăng ký</b>?';
            else if (err.code === 'auth/wrong-password' || err.code === 'auth/invalid-credential') msg = 'Sai mật khẩu. Bấm <b>Quên mật khẩu</b> để đặt lại.';
            else if (err.code === 'auth/invalid-email') msg = 'Email không đúng định dạng.';
            else if (err.code === 'auth/too-many-requests') msg = 'Bạn đã thử quá nhiều lần. Vui lòng đợi vài phút.';
            else if (err.code === 'auth/operation-not-allowed') msg = '⚠️ Chưa bật <b>Email/Password</b> trên Firebase Console.';
            showMsg('elfMsg', msg, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = orig;
        }
    }

    async function doEmailRegister(e) {
        if (e) e.preventDefault();
        var rawEmail = document.getElementById('elfRegEmail').value || '';
        var name = (document.getElementById('elfRegName').value || '').trim();
        var pwd = document.getElementById('elfRegPwd').value || '';
        var pwd2 = document.getElementById('elfRegPwd2').value || '';
        var btn = document.getElementById('elfRegisterSubmit');

        var res = normalizeGmailEmail(rawEmail);
        if (res.error) {
            showMsg('elfMsg', res.error, 'error');
            return;
        }
        var email = res.email;

        document.getElementById('elfRegEmail').value = email;
        updateEmailPreview('elfRegEmail', 'elfRegEmailPreview');

        if (pwd.length < 6) { showMsg('elfMsg', 'Mật khẩu phải từ 6 ký tự trở lên.', 'error'); return; }
        if (pwd !== pwd2) { showMsg('elfMsg', 'Mật khẩu nhập lại không khớp.', 'error'); return; }

        var orig = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="elf-spinner"></span> Đang tạo tài khoản...';

        try {
            var cred = await auth.createUserWithEmailAndPassword(email, pwd);
            if (name && cred.user) {
                try { await cred.user.updateProfile({ displayName: name }); } catch(_e) {}
            }
            showMsg('elfMsg', '✅ Tạo tài khoản thành công! Đang đăng nhập...', 'success');
            setTimeout(function() {
                try {
                    if (typeof hideLoginModal === 'function') hideLoginModal();
                    else {
                        var lm = document.getElementById('loginModal');
                        if (lm) lm.classList.remove('show');
                    }
                } catch(_e) {}
                clearMsg('elfMsg');
            }, 800);
        } catch (err) {
            console.error('[ELF Register]', err);
            var msg = 'Lỗi: ' + (err.code || err.message);
            if (err.code === 'auth/email-already-in-use') msg = 'Email này đã được đăng ký. Chuyển sang tab <b>Đăng nhập</b>.';
            else if (err.code === 'auth/weak-password') msg = 'Mật khẩu quá yếu.';
            else if (err.code === 'auth/operation-not-allowed') msg = '⚠️ Chưa bật <b>Email/Password</b> trên Firebase Console.';
            showMsg('elfMsg', msg, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = orig;
        }
    }

    async function doForgot() {
        var rawEmail = document.getElementById('elfLoginEmail').value || '';
        var res = normalizeGmailEmail(rawEmail);
        if (res.error) {
            showMsg('elfMsg', 'Vui lòng nhập email Gmail hợp lệ vào ô <b>Email</b> trước.', 'error');
            return;
        }
        var email = res.email;
        document.getElementById('elfLoginEmail').value = email;
        updateEmailPreview('elfLoginEmail', 'elfLoginEmailPreview');

        if (!confirm('Gửi email khôi phục mật khẩu đến:\n\n' + email + ' ?')) return;
        try {
            await auth.sendPasswordResetEmail(email);
            showMsg('elfMsg', '✅ Đã gửi email khôi phục!<br>Kiểm tra hộp thư (kể cả Spam).', 'success');
        } catch (err) {
            console.error('[ELF Forgot]', err);
            var msg = 'Lỗi: ' + (err.code || err.message);
            if (err.code === 'auth/user-not-found') msg = 'Không tìm thấy tài khoản với email này.';
            showMsg('elfMsg', msg, 'error');
        }
    }

    /* ============ INIT ============ */
    function initElf() {
        /* Set password modal bindings */
        var closeBtn = document.getElementById('elfSetPwdClose');
        if (closeBtn && !closeBtn.__elfBound) {
            closeBtn.__elfBound = true;
            closeBtn.addEventListener('click', closeSetPwdModal);
        }
        var modal = document.getElementById('elfSetPwdModal');
        if (modal && !modal.__elfBound) {
            modal.__elfBound = true;
            modal.addEventListener('click', function(e) { if (e.target === modal) closeSetPwdModal(); });
        }
        var skipBtn = document.getElementById('elfSetPwdSkip');
        if (skipBtn && !skipBtn.__elfBound) {
            skipBtn.__elfBound = true;
            skipBtn.addEventListener('click', closeSetPwdModal);
        }
        var form = document.getElementById('elfSetPwdForm');
        if (form && !form.__elfBound) {
            form.__elfBound = true;
            form.addEventListener('submit', handleSetPassword);
        }
        var pwd1 = document.getElementById('elfSetPwd1');
        if (pwd1 && !pwd1.__elfBound) {
            pwd1.__elfBound = true;
            pwd1.addEventListener('input', function() { updateStrength(this.value); });
        }

        /* Inject form email vào #loginModal (retry vì modal có thể render sau) */
        var tries = 0;
        var injectTimer = setInterval(function() {
            tries++;
            if (injectInlineForm() || tries > 40) clearInterval(injectTimer);
        }, 300);

        /* Hook auth */
        if (auth && !auth.__elfHooked) {
            auth.__elfHooked = true;
            auth.onAuthStateChanged(function(user) {
                checkAndAskSetPassword(user);
            });
        }

        /* ESC đóng modal set pwd */
        document.addEventListener('keydown', function(e) {
            if (e.key !== 'Escape') return;
            var m1 = document.getElementById('elfSetPwdModal');
            if (m1 && m1.classList.contains('show')) closeSetPwdModal();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() { waitAuth(initElf); });
    } else {
        waitAuth(initElf);
    }

    /* Debug */
    window.__elfDebug = {
        openSetPwd: openSetPwdModal,
        login: function(e, p) {
            document.getElementById('elfLoginEmail').value = e || '';
            document.getElementById('elfLoginPwd').value = p || '';
            doEmailLogin();
        },
        register: function(e, n, p) {
            document.getElementById('elfRegEmail').value = e || '';
            document.getElementById('elfRegName').value = n || '';
            document.getElementById('elfRegPwd').value = p || '';
            document.getElementById('elfRegPwd2').value = p || '';
            doEmailRegister();
        },
        normalize: function(v) { return normalizeGmailEmail(v); },
        hasPassword: function() { return auth && auth.currentUser ? userHasPassword(auth.currentUser) : false; },
        resetAskedFlag: function() {
            try {
                var u = auth.currentUser;
                if (u && u.email) sessionStorage.removeItem(PWD_ASKED_KEY + u.email.toLowerCase());
            } catch(e) {}
        }
    };

    console.log('[Login Fallback] Inline module + Gmail auto-fill loaded OK');
})();
"""


if __name__ == "__main__":
    css = build_login_fallback_css()
    html = build_login_fallback_html()
    js = build_login_fallback_js()
    print("CSS:  %d ký tự" % len(css))
    print("HTML: %d ký tự" % len(html))
    print("JS:   %d ký tự" % len(js))
    assert 'elfSetPwdModal' in html
    assert 'elfInlineForm' in js
    assert 'normalizeGmailEmail' in js
    assert 'signInWithEmailAndPassword' in js
    assert 'createUserWithEmailAndPassword' in js
    print("✅ Module sẵn sàng dùng")
