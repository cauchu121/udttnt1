// InsurTech Smart System - Frontend Application Logic (Xanh Lá & Trắng - 100% Tiếng Việt)
const API_BASE = window.location.origin.includes("5173") ? "http://127.0.0.1:8000/api/v1" : "/api/v1";

const DEMO_ACCOUNTS = {
  officer: {
    email: "officer@insurtech.vn",
    pass: "Officer@123",
    name: "Trần Thị Giám Định",
    role: "claims_officer",
    roleTitle: "Giám định viên",
    initials: "GĐ"
  },
  admin: {
    email: "admin@insurtech.vn",
    pass: "Admin@123",
    name: "Nguyễn Văn Quản Trị",
    role: "admin",
    roleTitle: "Quản trị viên",
    initials: "QT"
  },
  customer: {
    email: "customer@insurtech.vn",
    pass: "Customer@123",
    name: "Nguyễn Minh Quang",
    role: "customer",
    roleTitle: "Khách hàng",
    initials: "KH"
  },
  agent: {
    email: "agent@insurtech.vn",
    pass: "Agent@123",
    name: "Lê Hoàng Đại Lý",
    role: "agent",
    roleTitle: "Đại lý bảo hiểm",
    initials: "ĐL"
  }
};

let currentRoleKey = "officer";
let currentToken = "";
let currentUser = null;
let currentActiveClaim = null;

// Chuyển đổi định dạng tiền VNĐ
function formatVND(amount) {
  if (isNaN(amount) || amount === null) return "0 VNĐ";
  return new Intl.NumberFormat('vi-VN').format(amount) + " VNĐ";
}

// Định dạng số tiền có dấu chấm phân cách hàng nghìn (Ví dụ: 50.000.000)
function formatNumberWithDots(val) {
  if (val === null || val === undefined || val === "") return "";
  const cleanStr = val.toString().replace(/\D/g, "");
  if (!cleanStr) return "";
  const num = parseInt(cleanStr, 10);
  if (isNaN(num)) return "";
  return num.toLocaleString("vi-VN").replace(/,/g, ".");
}

// Chuyển chuỗi tiền có dấu chấm về dạng số thực (Ví dụ: "50.000.000" -> 50000000)
function parseNumberFromDots(val) {
  if (val === null || val === undefined || val === "") return 0;
  if (typeof val === "number") return val;
  const clean = val.toString().replace(/\./g, "").replace(/\D/g, "");
  return parseFloat(clean) || 0;
}

// Tự động định dạng dấu chấm giữa 3 số không ngay khi người dùng gõ
function formatCurrencyInput(inputEl) {
  if (!inputEl) return;
  const origVal = inputEl.value;
  const formatted = formatNumberWithDots(origVal);
  inputEl.value = formatted;
}

// Chuyển đổi mã trạng thái sang Tiếng Việt
function formatStatusBadge(status) {
  const map = {
    PENDING: { label: "Chờ thẩm định", class: "status-pending" },
    UNDER_REVIEW: { label: "Đang xem xét", class: "status-pending" },
    APPROVED: { label: "Đã phê duyệt", class: "status-approved" },
    REJECTED: { label: "Đã từ chối", class: "status-rejected" },
    ACTIVE: { label: "Đang hiệu lực", class: "status-active" },
    EXPIRED: { label: "Hết hiệu lực", class: "status-expired" },
    PAID: { label: "Đã nộp phí", class: "status-approved" }
  };
  const item = map[status] || { label: status, class: "status-pending" };
  return `<span class="status-pill ${item.class}">${item.label}</span>`;
}

// Hiển thị thông báo Toast
function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i> <span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Ẩn/Hiện mật khẩu
function togglePasswordVisibility(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon = document.getElementById(iconId);
  if (input.type === "password") {
    input.type = "text";
    icon.className = "bi bi-eye-slash";
  } else {
    input.type = "password";
    icon.className = "bi bi-eye";
  }
}

// =============================================================================
// XÁC THỰC: ĐĂNG NHẬP, ĐĂNG XUẤT VÀ PHÂN QUYỀN
// =============================================================================

// Điền tài khoản mẫu vào form đăng nhập
function selectRolePreset(roleKey, notify = false) {
  currentRoleKey = roleKey;
  const acc = DEMO_ACCOUNTS[roleKey];
  if (!acc) return;

  const emailInput = document.getElementById("loginEmailInput");
  const passInput = document.getElementById("loginPasswordInput");
  if (emailInput) emailInput.value = acc.email;
  if (passInput) passInput.value = acc.pass;

  if (notify) {
    showToast(`Đã chọn tài khoản: ${acc.roleTitle} (${acc.email})`);
  }
}

// Gửi form đăng nhập
async function submitLoginForm() {
  const email = document.getElementById("loginEmailInput").value.trim();
  const password = document.getElementById("loginPasswordInput").value;
  const btn = document.getElementById("btnLoginSubmit");
  const originalBtnHtml = btn.innerHTML;

  if (!email || !password) {
    showToast("Vui lòng nhập đầy đủ Email và Mật khẩu!", "error");
    return;
  }

  btn.disabled = true;
  btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Đang xác thực...`;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email, password: password })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Email hoặc mật khẩu không chính xác.");
    }

    const data = await res.json();
    currentToken = data.access_token;
    currentUser = data.user;

    const foundKey = Object.keys(DEMO_ACCOUNTS).find(k => DEMO_ACCOUNTS[k].email === currentUser.email) || "officer";
    currentRoleKey = foundKey;

    showToast(`Đăng nhập thành công! Chào mừng ${currentUser.full_name}.`);
    showAppView();

  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalBtnHtml;
  }
}

// Đăng xuất khỏi hệ thống
function handleLogout() {
  currentToken = "";
  currentUser = null;

  document.getElementById("mainAppContainer").style.display = "none";
  document.getElementById("loginScreen").style.display = "flex";

  selectRolePreset("officer", false);
  showToast("Bạn đã đăng xuất khỏi hệ thống thành công.");
}

// Hiển thị giao diện chính và áp dụng phân quyền
function showAppView() {
  document.getElementById("loginScreen").style.display = "none";
  document.getElementById("mainAppContainer").style.display = "flex";

  const acc = DEMO_ACCOUNTS[currentRoleKey] || { initials: "ND", roleTitle: "Người dùng" };
  document.getElementById("userAvatar").textContent = acc.initials;
  document.getElementById("userNameDisplay").textContent = currentUser.full_name;
  
  // Hiển thị vai trò bằng Tiếng Việt chuẩn
  document.getElementById("userRoleBadge").textContent = acc.roleTitle;

  applyRolePermissions(currentUser.role);
}

// Áp dụng giới hạn giao diện và phân quyền thao tác chi tiết theo vai trò (RBAC)
function applyRolePermissions(role) {
  const navDash = document.getElementById("navDashboard");
  const navClaims = document.getElementById("navClaims");
  const navPolicies = document.getElementById("navPolicies");
  const navProducts = document.getElementById("navProducts");
  const navFinance = document.getElementById("navFinance");
  const btnCreatePolicy = document.getElementById("btnCreatePolicy");
  const btnTopSubmitClaim = document.getElementById("btnTopSubmitClaim");

  // Cập nhật trạng thái active cho thanh 1-Click Role Switcher
  document.querySelectorAll(".role-nav-btn").forEach(b => {
    b.classList.remove("active", "role-officer", "role-customer", "role-agent", "role-admin");
  });
  const activeNavBtn = document.getElementById(`btnNavRole_${currentRoleKey}`);
  if (activeNavBtn) {
    activeNavBtn.classList.add("active", `role-${currentRoleKey}`);
  }

  // Cập nhật Banner Nhiệm Vụ & Thao Tác Riêng Biệt
  const bannerBadge = document.getElementById("missionBannerBadge");
  const bannerText = document.getElementById("missionBannerText");
  const banner = document.getElementById("roleMissionBanner");

  if (role === "claims_officer") {
    // 1. GIÁM ĐỊNH VIÊN (CLAIMS OFFICER)
    if (bannerBadge) {
      bannerBadge.className = "banner-role-tag banner-officer";
      bannerBadge.innerHTML = `<i class="bi bi-shield-check"></i> Giám Định Viên`;
    }
    if (banner) banner.style.borderLeftColor = "#0f766e";
    if (bannerText) {
      bannerText.innerHTML = `<strong>Thao tác độc quyền:</strong> Thẩm định hồ sơ viện phí, kích hoạt AI đối soát chi phí y tế và trực tiếp ký duyệt <strong>Phê duyệt / Từ chối bồi thường (Human-in-the-loop)</strong>.`;
    }

    if (navDash) navDash.style.display = "flex";
    if (navClaims) {
      navClaims.style.display = "flex";
      navClaims.innerHTML = `<i class="bi bi-file-earmark-medical-fill"></i> Thẩm Định Bồi Thường <span class="badge badge-pending" id="badgePendingClaims">2</span>`;
    }
    if (navPolicies) {
      navPolicies.style.display = "flex";
      navPolicies.innerHTML = `<i class="bi bi-journal-check"></i> Tra Cứu Hợp Đồng (Đối Soát)`;
    }
    if (navProducts) {
      navProducts.style.display = "flex";
      navProducts.innerHTML = `<i class="bi bi-box-seam-fill"></i> Bảng Quyền Lợi & Loại Trừ`;
    }
    if (navFinance) navFinance.style.display = "none"; // Giám định viên không làm kế toán

    if (btnTopSubmitClaim) btnTopSubmitClaim.style.display = "none";
    if (btnCreatePolicy) btnCreatePolicy.style.display = "none";

    switchTab("claims");

  } else if (role === "customer") {
    // 2. KHÁCH HÀNG (CUSTOMER)
    if (bannerBadge) {
      bannerBadge.className = "banner-role-tag banner-customer";
      bannerBadge.innerHTML = `<i class="bi bi-person"></i> Khách Hàng Thụ Hưởng`;
    }
    if (banner) banner.style.borderLeftColor = "#16a34a";
    if (bannerText) {
      bannerText.innerHTML = `<strong>Thao tác của Khách hàng:</strong> Quản lý hợp đồng bảo hiểm cá nhân, <strong>Nộp yêu cầu bồi thường trực tuyến</strong>, theo dõi tiến độ chi trả viện phí và lịch sử đóng phí.`;
    }

    if (navDash) navDash.style.display = "none"; // Không xem số liệu tài chính nội bộ công ty
    if (navClaims) {
      navClaims.style.display = "flex";
      navClaims.innerHTML = `<i class="bi bi-file-earmark-medical"></i> Hồ Sơ Bồi Thường Của Tôi`;
    }
    if (navPolicies) {
      navPolicies.style.display = "flex";
      navPolicies.innerHTML = `<i class="bi bi-shield-shaded"></i> Hợp Đồng Của Tôi`;
    }
    if (navProducts) {
      navProducts.style.display = "flex";
      navProducts.innerHTML = `<i class="bi bi-box-seam"></i> Khám Phá Gói Bảo Hiểm`;
    }
    if (navFinance) {
      navFinance.style.display = "flex";
      navFinance.innerHTML = `<i class="bi bi-cash-stack"></i> Lịch Sử Đóng Phí Của Tôi`;
    }

    if (btnTopSubmitClaim) {
      btnTopSubmitClaim.style.display = "inline-flex";
      btnTopSubmitClaim.innerHTML = `<i class="bi bi-plus-circle-fill"></i> Nộp Yêu Cầu Bồi Thường`;
    }
    if (btnCreatePolicy) {
      btnCreatePolicy.style.display = "inline-flex";
      btnCreatePolicy.innerHTML = `<i class="bi bi-cart-plus-fill"></i> Mua Thêm Gói Mới`;
    }

    switchTab("policies");

  } else if (role === "agent") {
    // 3. ĐẠI LÝ BẢO HIỂM (AGENT)
    if (bannerBadge) {
      bannerBadge.className = "banner-role-tag banner-agent";
      bannerBadge.innerHTML = `<i class="bi bi-briefcase"></i> Đại Lý Bảo Hiểm`;
    }
    if (banner) banner.style.borderLeftColor = "#d97706";
    if (bannerText) {
      bannerText.innerHTML = `<strong>Thao tác của Đại lý:</strong> Tư vấn gói sản phẩm, <strong>Cấp hợp đồng bảo hiểm mới cho khách hàng</strong> và hỗ trợ khách nộp hồ sơ yêu cầu bồi thường.`;
    }

    if (navDash) navDash.style.display = "none";
    if (navFinance) navFinance.style.display = "none";
    if (navProducts) {
      navProducts.style.display = "flex";
      navProducts.innerHTML = `<i class="bi bi-stars"></i> Danh Mục Tư Vấn Bán Hàng`;
    }
    if (navPolicies) {
      navPolicies.style.display = "flex";
      navPolicies.innerHTML = `<i class="bi bi-journal-check"></i> Quản Lý Hợp Đồng Khách`;
    }
    if (navClaims) {
      navClaims.style.display = "flex";
      navClaims.innerHTML = `<i class="bi bi-file-earmark-medical"></i> Hồ Sơ Claim Khách Hàng`;
    }

    if (btnTopSubmitClaim) {
      btnTopSubmitClaim.style.display = "inline-flex";
      btnTopSubmitClaim.innerHTML = `<i class="bi bi-people-fill"></i> Nộp Claim Hộ Khách`;
    }
    if (btnCreatePolicy) {
      btnCreatePolicy.style.display = "inline-flex";
      btnCreatePolicy.innerHTML = `<i class="bi bi-plus-lg"></i> Cấp Hợp Đồng Cho Khách`;
    }

    switchTab("products");

  } else if (role === "admin") {
    // 4. QUẢN TRỊ VIÊN (ADMIN)
    if (bannerBadge) {
      bannerBadge.className = "banner-role-tag banner-admin";
      bannerBadge.innerHTML = `<i class="bi bi-gear-fill"></i> Quản Trị Toàn Quyền`;
    }
    if (banner) banner.style.borderLeftColor = "#2563eb";
    if (bannerText) {
      bannerText.innerHTML = `<strong>Quyền hạn Quản trị:</strong> Giám sát toàn diện tỷ lệ tổn thất (Loss Ratio), doanh thu phí, cấp hợp đồng và giám sát bồi thường toàn hệ thống.`;
    }

    if (navDash) {
      navDash.style.display = "flex";
      navDash.innerHTML = `<i class="bi bi-grid-1x2-fill"></i> Tổng Quan & Loss Ratio`;
    }
    if (navClaims) {
      navClaims.style.display = "flex";
      navClaims.innerHTML = `<i class="bi bi-file-earmark-medical-fill"></i> Quản Lý Bồi Thường <span class="badge badge-pending" id="badgePendingClaims">2</span>`;
    }
    if (navPolicies) {
      navPolicies.style.display = "flex";
      navPolicies.innerHTML = `<i class="bi bi-journal-check"></i> Hợp Đồng Toàn Hệ Thống`;
    }
    if (navProducts) {
      navProducts.style.display = "flex";
      navProducts.innerHTML = `<i class="bi bi-box-seam-fill"></i> Danh Mục Sản Phẩm`;
    }
    if (navFinance) {
      navFinance.style.display = "flex";
      navFinance.innerHTML = `<i class="bi bi-cash-stack"></i> Kế Toán Thu Phí`;
    }

    if (btnTopSubmitClaim) btnTopSubmitClaim.style.display = "none";
    if (btnCreatePolicy) {
      btnCreatePolicy.style.display = "inline-flex";
      btnCreatePolicy.innerHTML = `<i class="bi bi-plus-lg"></i> Cấp Hợp Đồng Mới`;
    }

    switchTab("dashboard");
  }
}

// Chuyển nhanh vai trò 1-Click phục vụ kiểm thử
async function quickSwitchRole(roleKey) {
  const acc = DEMO_ACCOUNTS[roleKey];
  if (!acc) return;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: acc.email, password: acc.pass })
    });

    if (!res.ok) {
      throw new Error("Không thể chuyển đổi sang tài khoản: " + acc.roleTitle);
    }

    const data = await res.json();
    currentToken = data.access_token;
    currentUser = data.user;
    currentRoleKey = roleKey;

    showAppView();
    showToast(`Đã chuyển sang vai trò: ${acc.roleTitle} (${acc.name}). Giao diện và thao tác đã được tùy biến!`, "success");

  } catch (err) {
    showToast(err.message, "error");
  }
}

// =============================================================================
// ĐIỀU HƯỚNG TAB & TẢI DỮ LIỆU ĐỒNG BỘ TIẾNG VIỆT
// =============================================================================

function switchTab(tabId) {
  document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

  const targetBtn = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  const targetPane = document.getElementById(`tab-${tabId}`);
  if (targetBtn) targetBtn.classList.add("active");
  if (targetPane) targetPane.classList.add("active");

  // Đồng bộ tiêu đề và mô tả phụ 100% Tiếng Việt theo từng tab
  const titles = {
    dashboard: "Báo Cáo Thống Kê & Tỷ Lệ Tổn Thất (Loss Ratio)",
    claims: "Quản Lý & Thẩm Định Yêu Cầu Bồi Thường (Claims)",
    policies: "Quản Lý Danh Sách Hợp Đồng Bảo Hiểm",
    products: "Danh Mục Các Gói Sản Phẩm Bảo Hiểm",
    finance: "Quản Lý Thu Phí Bảo Hiểm Định Kỳ",
    chatbot: "Trợ Lý Ảo AI Advisor - Tư Vấn Quyền Lợi & Điều Khoản"
  };

  const subtitles = {
    dashboard: "Theo dõi doanh thu thu phí, chi trả bồi thường và giám sát an toàn tài chính thời gian thực.",
    claims: "Tiếp nhận hồ sơ bồi thường, đối soát viện phí y tế với điều khoản và phê duyệt chi trả.",
    policies: "Theo dõi thời hạn hiệu lực, hạn mức bảo vệ tối đa và chu kỳ đóng phí định kỳ.",
    products: "Chi tiết quyền lợi bảo hiểm, hạn mức chi trả tối đa và biểu phí thường niên chuẩn.",
    finance: "Nhật ký thanh toán phí bảo hiểm theo kỳ và lịch sử giao dịch khách hàng.",
    chatbot: "Tư vấn gói bảo hiểm tối ưu, giải đáp quy tắc quyền lợi và điều khoản loại trừ 24/7."
  };

  document.getElementById("pageTitle").textContent = titles[tabId] || "Hệ Thống InsurTech";
  document.getElementById("pageSubtitle").textContent = subtitles[tabId] || "";

  if (tabId === "dashboard") loadDashboard();
  if (tabId === "claims") loadClaims();
  if (tabId === "policies") loadPolicies();
  if (tabId === "products") loadProducts();
  if (tabId === "finance") loadPayments();
}

async function refreshCurrentTab() {
  const btn = document.getElementById("btnRefreshTab");
  const icon = btn ? btn.querySelector("i") : null;
  if (icon) icon.classList.add("spin-icon");
  if (btn) btn.disabled = true;

  try {
    const activePane = document.querySelector(".tab-pane.active");
    const tabId = activePane ? activePane.id.replace("tab-", "") : "dashboard";

    if (tabId === "dashboard") await loadDashboard();
    else if (tabId === "claims") await loadClaims();
    else if (tabId === "policies") await loadPolicies();
    else if (tabId === "products") await loadProducts();
    else if (tabId === "finance") await loadPayments();
    else if (tabId === "chatbot") {
      showToast("Kênh Trợ lý AI Advisor luôn kết nối trực tuyến sẵn sàng!");
    }

    // Luôn cập nhật số lượng hồ sơ chờ duyệt cho badge
    try {
      const res = await fetch(`${API_BASE}/claims?status=PENDING`, {
        headers: { "Authorization": `Bearer ${currentToken}` }
      });
      if (res.ok) {
        const pendingClaims = await res.json();
        const badge = document.getElementById("badgePendingClaims");
        if (badge) badge.textContent = pendingClaims.length;
      }
    } catch (_) {}

    const tabNames = {
      dashboard: "Báo cáo thống kê & Loss Ratio",
      claims: "Danh sách hồ sơ bồi thường (Claims)",
      policies: "Danh sách hợp đồng bảo hiểm",
      products: "Danh mục các gói sản phẩm",
      finance: "Nhật ký thu phí định kỳ",
      chatbot: "Trợ lý AI Advisor"
    };

    showToast(`Đã làm mới dữ liệu ${tabNames[tabId] || ''} thành công!`);
  } catch (err) {
    showToast("Đã làm mới dữ liệu hệ thống!");
  } finally {
    setTimeout(() => {
      if (icon) icon.classList.remove("spin-icon");
      if (btn) btn.disabled = false;
    }, 600);
  }
}

// 1. THỐNG KÊ DASHBOARD (LOSS RATIO)
async function loadDashboard() {
  if (currentUser && currentUser.role !== "admin" && currentUser.role !== "claims_officer") {
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/analytics/dashboard`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("kpiActivePolicies").textContent = data.total_active_policies;
    document.getElementById("kpiTotalPremiums").textContent = formatVND(data.total_premiums_written);
    document.getElementById("kpiTotalClaims").textContent = formatVND(data.total_claims_paid);
    document.getElementById("kpiClaimsCount").textContent = `${data.total_claims_count} hồ sơ (${data.pending_claims_count} chờ duyệt)`;
    document.getElementById("kpiLossRatio").textContent = `${data.loss_ratio_percent}%`;

    const sub = document.getElementById("kpiLossRatioSub");
    if (data.loss_ratio_percent > 70) {
      sub.innerHTML = `<span class="text-danger fw-bold"><i class="bi bi-exclamation-triangle"></i> Nguy cơ rủi ro cao (&gt; 70%)</span>`;
    } else {
      sub.innerHTML = `<span class="text-success"><i class="bi bi-shield-check"></i> Trong ngưỡng an toàn (&lt; 65%)</span>`;
    }

    // Biểu đồ cột xu hướng tháng
    const chartContainer = document.getElementById("chartMonthlyBars");
    chartContainer.innerHTML = "";
    const maxVal = Math.max(...data.monthly_trend.map(m => Math.max(m.premiums, m.claims)), 1000000);

    data.monthly_trend.forEach(m => {
      const pHeight = Math.round((m.premiums / maxVal) * 160);
      const cHeight = Math.round((m.claims / maxVal) * 160);
      const group = document.createElement("div");
      group.className = "chart-bar-group";
      group.innerHTML = `
        <div class="bars-wrapper">
          <div class="bar-premium" style="height: ${pHeight}px" title="Thu phí: ${formatVND(m.premiums)}"></div>
          <div class="bar-claim" style="height: ${cHeight}px" title="Bồi thường: ${formatVND(m.claims)}"></div>
        </div>
        <span class="bar-label">${m.month}</span>
      `;
      chartContainer.appendChild(group);
    });

    // Cơ cấu sản phẩm
    const distContainer = document.getElementById("chartDistribution");
    distContainer.innerHTML = "";
    data.category_distribution.forEach(d => {
      const item = document.createElement("div");
      item.className = "dist-item";
      item.innerHTML = `
        <div class="dist-info">
          <span>${d.category}</span>
          <span class="text-success fw-bold">${d.value}%</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-fill" style="width: ${d.value}%"></div>
        </div>
      `;
      distContainer.appendChild(item);
    });
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

// 2. QUẢN LÝ BỒI THƯỜNG (CLAIMS)
async function loadClaims() {
  const statusFilter = document.getElementById("claimsFilterStatus").value;
  let url = `${API_BASE}/claims`;
  if (statusFilter) url += `?status=${statusFilter}`;

  try {
    const res = await fetch(url, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (!res.ok) throw new Error("Lỗi tải danh sách hồ sơ");
    const claims = await res.json();

    const tbody = document.getElementById("claimsTableBody");
    tbody.innerHTML = "";

    const pendingCount = claims.filter(c => c.status === "PENDING").length;
    const badge = document.getElementById("badgePendingClaims");
    if (badge) badge.textContent = pendingCount;

    if (claims.length === 0) {
      const msg = currentUser.role === "customer" 
        ? "Bạn chưa có hồ sơ yêu cầu bồi thường nào. Bấm 'Nộp Yêu Cầu Bồi Thường' để gửi viện phí."
        : "Không có hồ sơ bồi thường nào trong hệ thống.";
      tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">${msg}</td></tr>`;
      return;
    }

    claims.forEach(c => {
      const tr = document.createElement("tr");
      const statusBadge = formatStatusBadge(c.status);

      // Thao tác phân quyền khác nhau 100% theo từng vai trò
      let actionButtons = ``;
      if (currentUser.role === "claims_officer" || currentUser.role === "admin") {
        // Giám định viên & Admin: Độc quyền thẩm định AI và ra quyết định
        if (c.status === "PENDING") {
          actionButtons = `
            <button class="btn btn-red btn-sm shadow-sm" onclick="triggerAiAssessment(${c.id})" title="Kích hoạt AI đối soát hóa đơn và duyệt chi trả">
              <i class="bi bi-stars"></i> ✨ Thẩm định AI
            </button>
          `;
        } else {
          actionButtons = `
            <button class="btn btn-outline btn-sm" onclick="triggerAiAssessment(${c.id})" title="Xem lại kết quả và điều chỉnh số tiền duyệt">
              <i class="bi bi-eye"></i> Xem & Điều chỉnh
            </button>
          `;
        }
      } else if (currentUser.role === "customer") {
        // Khách hàng: Chỉ xem giải trình kết quả bồi thường cá nhân (Read-only)
        if (c.status === "PENDING") {
          actionButtons = `
            <button class="btn btn-outline btn-sm text-muted" onclick="viewClaimResult(${c.id})" title="Xem tình trạng tiếp nhận">
              <i class="bi bi-clock-history"></i> Đang chờ giám định
            </button>
          `;
        } else if (c.status === "APPROVED") {
          actionButtons = `
            <button class="btn btn-success btn-sm shadow-sm" onclick="viewClaimResult(${c.id})" title="Xem chi tiết số tiền được bồi thường">
              <i class="bi bi-check-circle-fill"></i> Xem tiền bồi thường
            </button>
          `;
        } else {
          actionButtons = `
            <button class="btn btn-danger btn-sm" onclick="viewClaimResult(${c.id})" title="Xem lý do từ chối chi trả">
              <i class="bi bi-x-circle-fill"></i> Xem lý do từ chối
            </button>
          `;
        }
      } else if (currentUser.role === "agent") {
        // Đại lý: Theo dõi tiến độ để trả lời khách hàng (Read-only)
        actionButtons = `
          <button class="btn btn-outline btn-sm" onclick="viewClaimResult(${c.id})" title="Xem tiến độ giải quyết để hỗ trợ khách hàng">
            <i class="bi bi-search"></i> Tiến độ bồi thường
          </button>
        `;
      }

      tr.innerHTML = `
        <td><strong class="text-success">${c.claim_number}</strong></td>
        <td><strong>${c.customer_name || 'Khách hàng'}</strong></td>
        <td>${c.product_name || 'Gói chuẩn'}</td>
        <td style="max-width: 200px;" title="${c.diagnosis}">${c.diagnosis}</td>
        <td><strong>${formatVND(c.claimed_amount)}</strong></td>
        <td class="text-success font-weight-bold">${formatVND(c.approved_amount)}</td>
        <td>${statusBadge}</td>
        <td>${actionButtons}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error(err);
  }
}

// 3. AI THẨM ĐỊNH BỒI THƯỜNG (DÀNH CHO GIÁM ĐỊNH VIÊN & ADMIN)
async function triggerAiAssessment(claimId) {
  const modal = document.getElementById("aiAssessmentModal");
  modal.style.display = "flex";
  document.getElementById("aiModalLoader").style.display = "flex";
  document.getElementById("aiModalContent").style.display = "none";
  document.getElementById("btnConfirmDecision").style.display = "none";
  const btnReject = document.getElementById("btnRejectDecision");
  if (btnReject) btnReject.style.display = "none";

  // Hiển thị form Giám định viên, ẩn khối kết quả xem nhanh của khách
  const offSec = document.getElementById("officerDecisionSection");
  if (offSec) offSec.style.display = "block";
  const custSec = document.getElementById("customerReadOnlyResultSection");
  if (custSec) custSec.style.display = "none";

  try {
    const claimRes = await fetch(`${API_BASE}/claims/${claimId}`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    currentActiveClaim = await claimRes.json();

    document.getElementById("modalClaimNumber").textContent = currentActiveClaim.claim_number;
    document.getElementById("modalMaxLimit").textContent = formatVND(50000000);

    const aiRes = await fetch(`${API_BASE}/ai/claim-assessment`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({ claim_id: claimId })
    });

    if (!aiRes.ok) {
      const errData = await aiRes.json();
      throw new Error(errData.detail || "Lỗi dịch vụ AI");
    }

    const aiData = await aiRes.json();

    document.getElementById("aiDisplayClaimed").textContent = formatVND(currentActiveClaim.claimed_amount);
    document.getElementById("aiDisplayRecommended").textContent = formatVND(aiData.recommended_amount);
    document.getElementById("aiDisplayFraudScore").textContent = `${aiData.fraud_risk_score} / 100`;

    const riskLevelTag = document.getElementById("aiDisplayRiskLevel");
    riskLevelTag.textContent = aiData.risk_level;
    if (aiData.fraud_risk_score > 50) {
      riskLevelTag.style.background = "#fee2e2";
      riskLevelTag.style.color = "#991b1b";
    } else {
      riskLevelTag.style.background = "#dcfce7";
      riskLevelTag.style.color = "#15803d";
    }

    // Khoản duyệt
    const approvedUl = document.getElementById("aiApprovedItemsList");
    approvedUl.innerHTML = "";
    if (aiData.approved_items && aiData.approved_items.length > 0) {
      aiData.approved_items.forEach(item => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${item.item_name}:</strong> ${formatVND(item.amount)}<br><small class="text-muted">${item.reason}</small>`;
        approvedUl.appendChild(li);
      });
    } else {
      approvedUl.innerHTML = `<li>Chưa có chi tiết khoản mục.</li>`;
    }

    // Khoản loại trừ
    const rejectedUl = document.getElementById("aiRejectedItemsList");
    rejectedUl.innerHTML = "";
    if (aiData.rejected_items && aiData.rejected_items.length > 0) {
      aiData.rejected_items.forEach(item => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${item.item_name}:</strong> ${formatVND(item.amount)}<br><small class="text-danger">${item.rejection_reason}</small>`;
        rejectedUl.appendChild(li);
      });
    } else {
      rejectedUl.innerHTML = `<li class="text-muted">Không có khoản mục nào bị loại trừ.</li>`;
    }

    document.getElementById("aiAssessmentConclusionText").textContent = aiData.assessment_conclusion;
    const fraudBox = document.getElementById("aiFraudSignalsBox");
    fraudBox.innerHTML = "";
    if (aiData.fraud_warning_signals && aiData.fraud_warning_signals.length > 0) {
      aiData.fraud_warning_signals.forEach(sig => {
        fraudBox.innerHTML += `<div class="badge badge-info mb-1"><i class="bi bi-shield-exclamation"></i> ${sig}</div>`;
      });
    }

    document.getElementById("officerFinalAmountInput").value = formatNumberWithDots(aiData.recommended_amount);
    document.getElementById("officerStatusSelect").value = "APPROVED";
    document.getElementById("officerNotesTextarea").value = `Duyệt theo đề xuất thẩm định AI Copilot: ${aiData.assessment_conclusion}`;

    document.getElementById("aiModalLoader").style.display = "none";
    document.getElementById("aiModalContent").style.display = "block";
    document.getElementById("btnConfirmDecision").style.display = "inline-flex";
    const btnReject = document.getElementById("btnRejectDecision");
    if (btnReject) btnReject.style.display = "inline-flex";

  } catch (err) {
    document.getElementById("aiModalLoader").innerHTML = `
      <div class="text-danger">
        <i class="bi bi-exclamation-triangle-fill" style="font-size: 32px"></i>
        <p class="mt-2 fw-bold">Không thể hoàn tất thẩm định AI: ${err.message}</p>
        <button class="btn btn-outline mt-3" onclick="closeAiModal()">Đóng</button>
      </div>
    `;
  }
}

// XEM KẾT QUẢ CHI TRẢ BỒI THƯỜNG (DÀNH CHO KHÁCH HÀNG & ĐẠI LÝ - READ-ONLY)
async function viewClaimResult(claimId) {
  const modal = document.getElementById("aiAssessmentModal");
  modal.style.display = "flex";
  document.getElementById("aiModalLoader").style.display = "none";
  document.getElementById("aiModalContent").style.display = "block";

  const offSec = document.getElementById("officerDecisionSection");
  if (offSec) offSec.style.display = "none";
  const custSec = document.getElementById("customerReadOnlyResultSection");
  if (custSec) custSec.style.display = "block";

  document.getElementById("btnConfirmDecision").style.display = "none";
  const btnReject = document.getElementById("btnRejectDecision");
  if (btnReject) btnReject.style.display = "none";

  try {
    const claimRes = await fetch(`${API_BASE}/claims/${claimId}`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    const c = await claimRes.json();
    currentActiveClaim = c;

    document.getElementById("modalClaimNumber").textContent = c.claim_number;
    document.getElementById("modalMaxLimit").textContent = formatVND(50000000);

    document.getElementById("aiDisplayClaimed").textContent = formatVND(c.claimed_amount);
    document.getElementById("aiDisplayRecommended").textContent = formatVND(c.approved_amount);
    document.getElementById("aiDisplayFraudScore").textContent = c.fraud_risk_score > 0 ? `${c.fraud_risk_score} / 100` : "An toàn";

    const riskLevelTag = document.getElementById("aiDisplayRiskLevel");
    riskLevelTag.textContent = c.status === "APPROVED" ? "Đã duyệt chi trả" : (c.status === "REJECTED" ? "Từ chối bồi thường" : "Đang thẩm định");
    riskLevelTag.style.background = c.status === "APPROVED" ? "#dcfce7" : (c.status === "REJECTED" ? "#fee2e2" : "#f1f5f9");
    riskLevelTag.style.color = c.status === "APPROVED" ? "#15803d" : (c.status === "REJECTED" ? "#991b1b" : "#475569");

    document.getElementById("customerViewStatus").textContent = c.status === "APPROVED" ? "ĐÃ PHÊ DUYỆT CHI TRẢ" : (c.status === "REJECTED" ? "TỪ CHỐI CHI TRẢ" : "ĐANG XEM XÉT");
    document.getElementById("customerViewAmount").textContent = formatVND(c.approved_amount);
    document.getElementById("customerViewNotes").textContent = c.officer_notes || c.ai_assessment_notes || "Hồ sơ đang trong quy trình đối soát chứng từ y tế của Giám định viên.";

    document.getElementById("aiAssessmentConclusionText").textContent = c.ai_assessment_notes || (c.status === "APPROVED" ? `Hồ sơ đã được phê duyệt chi trả số tiền ${formatVND(c.approved_amount)}.` : "Hồ sơ đang được Ban Giám Định xử lý.");
    document.getElementById("aiFraudSignalsBox").innerHTML = "";

    const approvedUl = document.getElementById("aiApprovedItemsList");
    approvedUl.innerHTML = c.status === "APPROVED" ? `<li><strong class="text-success">Chi phí y tế được bồi thường:</strong> ${formatVND(c.approved_amount)}</li>` : `<li class="text-muted">Chưa có quyết định phê duyệt.</li>`;

    const rejectedUl = document.getElementById("aiRejectedItemsList");
    rejectedUl.innerHTML = c.status === "REJECTED" ? `<li class="text-danger">Không đủ điều kiện chi trả theo Quy tắc điều khoản bảo hiểm.</li>` : `<li class="text-muted">Không có khoản mục nào bị loại trừ.</li>`;

  } catch (err) {
    showToast(err.message, "error");
  }
}

// Lưu quyết định chi trả bồi thường (Phê duyệt hoặc Từ chối duyệt)
async function submitClaimDecision(targetStatus) {
  if (!currentActiveClaim) return;
  const status = targetStatus || document.getElementById("officerStatusSelect").value;
  let approvedAmount = parseNumberFromDots(document.getElementById("officerFinalAmountInput").value);
  if (status === "REJECTED") {
    approvedAmount = 0.0;
  }
  let notes = document.getElementById("officerNotesTextarea").value.trim();
  if (status === "REJECTED" && (!notes || notes.startsWith("Duyệt"))) {
    notes = "Giám định viên từ chối chi trả bồi thường sau khi thẩm định.";
  }

  try {
    const res = await fetch(`${API_BASE}/claims/${currentActiveClaim.id}/decision`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({
        approved_amount: approvedAmount,
        status: status,
        officer_notes: notes
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Xác nhận quyết định thất bại");
    }

    const actionName = status === "APPROVED" ? "Phê duyệt" : "Từ chối duyệt";
    showToast(`Đã ${actionName} hồ sơ ${currentActiveClaim.claim_number} thành công!`);
    closeAiModal();
    loadClaims();
    loadDashboard();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function approveOfficialDecision() {
  document.getElementById("officerStatusSelect").value = "APPROVED";
  submitClaimDecision("APPROVED");
}

function rejectOfficialDecision() {
  document.getElementById("officerStatusSelect").value = "REJECTED";
  document.getElementById("officerFinalAmountInput").value = 0;
  submitClaimDecision("REJECTED");
}

function confirmOfficialDecision() {
  submitClaimDecision();
}

function closeAiModal() {
  document.getElementById("aiAssessmentModal").style.display = "none";
  currentActiveClaim = null;
}

// 4. HỢP ĐỒNG BẢO HIỂM
let cachedProductsList = [];

async function loadPolicies() {
  try {
    const res = await fetch(`${API_BASE}/policies`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    const policies = await res.json();
    const tbody = document.getElementById("policiesTableBody");
    tbody.innerHTML = "";

    if (policies.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Chưa có hợp đồng bảo hiểm nào.</td></tr>`;
      return;
    }

    policies.forEach(p => {
      const tr = document.createElement("tr");
      const statusPill = formatStatusBadge(p.status);
      const cycleMap = {
        ANNUALLY: "năm",
        QUARTERLY: "quý",
        MONTHLY: "tháng"
      };
      const cycleUnit = cycleMap[p.payment_cycle] || "năm";

      tr.innerHTML = `
        <td><strong class="text-success">${p.policy_number}</strong></td>
        <td><strong>${p.customer_name || 'Khách hàng'}</strong></td>
        <td>${p.product_name || 'Gói chuẩn'}</td>
        <td>${formatVND(p.total_sum_insured)}</td>
        <td><strong>${formatVND(p.premium_amount)}</strong> / ${cycleUnit}</td>
        <td>${new Date(p.end_date).toLocaleDateString('vi-VN')}</td>
        <td>${statusPill}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error(err);
  }
}

let currentCustomerEntryMode = "free";

// Chuyển đổi giữa chế độ Nhập tự do và Chọn khách hàng có sẵn
function setCustomerEntryMode(mode) {
  currentCustomerEntryMode = mode;
  const btnFree = document.getElementById("btnModeFreeEntry");
  const btnSelect = document.getElementById("btnModeSelectExisting");
  const secFree = document.getElementById("customerFreeEntrySection");
  const secSelect = document.getElementById("customerSelectSection");

  if (mode === "free") {
    if (btnFree) btnFree.classList.add("active");
    if (btnSelect) btnSelect.classList.remove("active");
    if (secFree) secFree.style.display = "block";
    if (secSelect) secSelect.style.display = "none";
  } else {
    if (btnFree) btnFree.classList.remove("active");
    if (btnSelect) btnSelect.classList.add("active");
    if (secFree) secFree.style.display = "none";
    if (secSelect) secSelect.style.display = "block";
  }
}

// Mở Modal Cấp Hợp Đồng Mới
async function openCreatePolicyModal() {
  const modal = document.getElementById("createPolicyModal");
  if (!modal) return;

  const customerSelect = document.getElementById("policyCustomerSelect");
  const productSelect = document.getElementById("policyProductSelect");
  const startDateInput = document.getElementById("policyStartDate");
  const endDateInput = document.getElementById("policyEndDate");
  const toggleContainer = document.getElementById("customerEntryModeToggle");

  const nameInput = document.getElementById("policyCustomerNameInput");
  const identityInput = document.getElementById("policyCustomerIdentityInput");
  const phoneInput = document.getElementById("policyCustomerPhoneInput");
  const emailInput = document.getElementById("policyCustomerEmailInput");

  // Thiết lập ngày mặc định: Hôm nay và +1 năm
  const today = new Date();
  const nextYear = new Date();
  nextYear.setFullYear(today.getFullYear() + 1);

  startDateInput.value = today.toISOString().split("T")[0];
  endDateInput.value = nextYear.toISOString().split("T")[0];

  customerSelect.innerHTML = `<option value="">-- Đang nạp danh sách khách hàng... --</option>`;
  productSelect.innerHTML = `<option value="">-- Đang nạp danh mục gói sản phẩm... --</option>`;

  // Cấu hình chế độ nhập liệu theo vai trò người dùng
  if (currentUser && currentUser.role === "customer") {
    // Khách hàng tự mua gói cho chính mình
    if (toggleContainer) toggleContainer.style.display = "none";
    setCustomerEntryMode("free");
    if (nameInput) { nameInput.value = currentUser.full_name; nameInput.readOnly = true; }
    if (identityInput) { identityInput.value = currentUser.identity_card || ""; nameInput.readOnly = true; }
    if (phoneInput) { phoneInput.value = currentUser.phone || ""; phoneInput.readOnly = true; }
    if (emailInput) { emailInput.value = currentUser.email || ""; emailInput.readOnly = true; }
  } else {
    // Đại lý hoặc Quản trị viên: Tự do nhập thông tin khách hàng mới
    if (toggleContainer) toggleContainer.style.display = "inline-flex";
    setCustomerEntryMode("free");
    if (nameInput) { nameInput.value = ""; nameInput.readOnly = false; }
    if (identityInput) { identityInput.value = ""; identityInput.readOnly = false; }
    if (phoneInput) { phoneInput.value = ""; phoneInput.readOnly = false; }
    if (emailInput) { emailInput.value = ""; emailInput.readOnly = false; }
  }

  modal.style.display = "flex";

  try {
    // 1. Tải danh sách khách hàng (cho chế độ chọn có sẵn)
    let usersList = [];
    if (currentUser && currentUser.role === "customer") {
      usersList = [currentUser];
    } else {
      try {
        const uRes = await fetch(`${API_BASE}/auth/users?role=customer`, {
          headers: { "Authorization": `Bearer ${currentToken}` }
        });
        if (uRes.ok) {
          usersList = await uRes.json();
        }
      } catch (_) {}
      if (usersList.length === 0 && currentUser) {
        usersList = [currentUser];
      }
    }

    let customerOptions = usersList.filter(u => u.role === "customer");
    if (customerOptions.length === 0) {
      customerOptions = usersList;
    }

    customerSelect.innerHTML = "";
    customerOptions.forEach(u => {
      const opt = document.createElement("option");
      opt.value = u.id;
      opt.textContent = `${u.full_name} (${u.email} - CCCD: ${u.identity_card || 'Chưa cập nhật'})`;
      if (currentUser && currentUser.role === "customer" && u.id === currentUser.id) {
        opt.selected = true;
      }
      customerSelect.appendChild(opt);
    });

    // 2. Tải danh sách gói sản phẩm
    const pRes = await fetch(`${API_BASE}/policies/products`);
    if (pRes.ok) {
      cachedProductsList = await pRes.json();
    } else {
      cachedProductsList = [];
    }

    productSelect.innerHTML = "";
    if (cachedProductsList.length === 0) {
      productSelect.innerHTML = `<option value="">Không có gói sản phẩm nào</option>`;
    } else {
      cachedProductsList.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.product_name} (${p.category}) - ${formatNumberWithDots(p.max_coverage_limit)} VNĐ`;
        productSelect.appendChild(opt);
      });
      onPolicyProductSelected();
    }
  } catch (err) {
    showToast("Không thể tải thông tin khởi tạo: " + err.message, "error");
  }
}

// Đóng Modal Cấp Hợp Đồng Mới
function closeCreatePolicyModal() {
  const modal = document.getElementById("createPolicyModal");
  if (modal) modal.style.display = "none";
}

// Khi chọn gói sản phẩm, tự động cập nhật hạn mức và mức phí mẫu
function onPolicyProductSelected() {
  const productSelect = document.getElementById("policyProductSelect");
  const sumInsuredInput = document.getElementById("policySumInsured");

  const selectedId = parseInt(productSelect.value);
  const found = cachedProductsList.find(p => p.id === selectedId);
  if (found) {
    sumInsuredInput.value = formatNumberWithDots(found.max_coverage_limit);
    onPaymentCycleChange();
  }
}

// Khi thay đổi kỳ nộp phí, tự động tính toán lại mức phí định kỳ theo chu kỳ
function onPaymentCycleChange() {
  const productSelect = document.getElementById("policyProductSelect");
  const cycleSelect = document.getElementById("policyPaymentCycle");
  const premiumInput = document.getElementById("policyPremiumAmount");
  if (!productSelect || !cycleSelect || !premiumInput) return;

  const selectedId = parseInt(productSelect.value);
  const found = cachedProductsList.find(p => p.id === selectedId);
  if (!found) return;

  const cycle = cycleSelect.value;
  let calcPremium = found.base_annual_premium;
  if (cycle === "QUARTERLY") {
    calcPremium = Math.round(found.base_annual_premium * 0.27);
  } else if (cycle === "MONTHLY") {
    calcPremium = Math.round(found.base_annual_premium * 0.095);
  }
  premiumInput.value = formatNumberWithDots(calcPremium);
}

// Khi đổi ngày bắt đầu, tự động cộng 1 năm cho ngày kết thúc
function onPolicyStartDateChange() {
  const startDateInput = document.getElementById("policyStartDate");
  const endDateInput = document.getElementById("policyEndDate");
  if (!startDateInput.value) return;

  const start = new Date(startDateInput.value);
  if (!isNaN(start.getTime())) {
    const end = new Date(start);
    end.setFullYear(end.getFullYear() + 1);
    endDateInput.value = end.toISOString().split("T")[0];
  }
}

// Gửi form phát hành hợp đồng bảo hiểm mới (Hỗ trợ Nhập tự do HOẶC Chọn có sẵn)
async function handleCreatePolicySubmit() {
  const productId = parseInt(document.getElementById("policyProductSelect").value);
  const sumInsured = parseNumberFromDots(document.getElementById("policySumInsured").value);
  const premiumAmount = parseNumberFromDots(document.getElementById("policyPremiumAmount").value);
  const paymentCycle = document.getElementById("policyPaymentCycle").value;
  const startDate = document.getElementById("policyStartDate").value;
  const endDate = document.getElementById("policyEndDate").value;

  const btnSubmit = document.getElementById("btnSubmitCreatePolicy");
  const originalBtnHtml = btnSubmit ? btnSubmit.innerHTML : "";

  if (!productId) {
    showToast("Vui lòng chọn Gói bảo hiểm cần phát hành!", "error");
    return;
  }

  let customerId = null;
  let customerName = null;
  let customerIdentity = null;
  let customerPhone = null;
  let customerEmail = null;

  if (currentUser && currentUser.role === "customer") {
    customerId = currentUser.id;
  } else if (currentCustomerEntryMode === "free") {
    customerName = (document.getElementById("policyCustomerNameInput").value || "").trim();
    customerIdentity = (document.getElementById("policyCustomerIdentityInput").value || "").trim();
    customerPhone = (document.getElementById("policyCustomerPhoneInput").value || "").trim();
    customerEmail = (document.getElementById("policyCustomerEmailInput").value || "").trim();

    if (!customerName) {
      showToast("Vui lòng nhập Họ và tên khách hàng thụ hưởng!", "error");
      document.getElementById("policyCustomerNameInput").focus();
      return;
    }
    if (!customerIdentity) {
      showToast("Vui lòng nhập Số CCCD/CMND của khách hàng để định danh!", "error");
      document.getElementById("policyCustomerIdentityInput").focus();
      return;
    }
  } else {
    customerId = parseInt(document.getElementById("policyCustomerSelect").value);
    if (!customerId) {
      showToast("Vui lòng chọn một khách hàng từ danh sách!", "error");
      return;
    }
  }

  if (isNaN(sumInsured) || sumInsured <= 0 || isNaN(premiumAmount) || premiumAmount <= 0) {
    showToast("Hạn mức và phí bảo hiểm phải là số dương hợp lệ!", "error");
    return;
  }

  if (btnSubmit) {
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Đang phát hành...`;
  }

  try {
    const payload = {
      customer_id: customerId,
      customer_name: customerName,
      customer_identity: customerIdentity,
      customer_phone: customerPhone,
      customer_email: customerEmail,
      product_id: productId,
      start_date: startDate ? `${startDate}T00:00:00` : null,
      end_date: endDate ? `${endDate}T23:59:59` : null,
      total_sum_insured: sumInsured,
      premium_amount: premiumAmount,
      payment_cycle: paymentCycle
    };

    const res = await fetch(`${API_BASE}/policies`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Phát hành hợp đồng bảo hiểm thất bại.");
    }

    const newPol = await res.json();
    showToast(`Phát hành hợp đồng thành công cho khách hàng ${newPol.customer_name}! Số hợp đồng: ${newPol.policy_number}`, "success");

    closeCreatePolicyModal();
    loadPolicies();
    loadDashboard();

  } catch (err) {
    showToast(err.message, "error");
  } finally {
    if (btnSubmit) {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = originalBtnHtml;
    }
  }
}

// 5. GÓI SẢN PHẨM BẢO HIỂM
async function loadProducts() {
  try {
    const res = await fetch(`${API_BASE}/policies/products`);
    const products = await res.json();
    const container = document.getElementById("productsGridContainer");
    container.innerHTML = "";

    products.forEach(prd => {
      const card = document.createElement("div");
      card.className = "product-card";

      // Nút hành động khác biệt 100% theo từng vai trò
      let actionButtons = ``;
      if (currentUser && currentUser.role === "customer") {
        actionButtons = `
          <button class="btn btn-primary w-100 mb-2" onclick="openBuyProduct(${prd.id})">
            <i class="bi bi-cart-plus-fill"></i> Đăng Ký Mua Gói Này
          </button>
          <button class="btn btn-outline w-100" onclick="showProductDetails(${prd.id})">
            <i class="bi bi-file-text"></i> Xem Quyền Lợi Chi Tiết
          </button>
        `;
      } else if (currentUser && currentUser.role === "agent") {
        actionButtons = `
          <button class="btn btn-primary w-100 mb-2" onclick="openAgentIssueForProduct(${prd.id})">
            <i class="bi bi-person-plus-fill"></i> Tư Vấn & Cấp Cho Khách
          </button>
          <button class="btn btn-outline w-100" onclick="showProductDetails(${prd.id})">
            <i class="bi bi-file-text"></i> Bảng Quyền Lợi & Phí
          </button>
        `;
      } else if (currentUser && currentUser.role === "claims_officer") {
        actionButtons = `
          <button class="btn btn-outline w-100" onclick="showProductDetails(${prd.id})">
            <i class="bi bi-file-earmark-ruled"></i> Căn Cứ Điều Khoản & Điểm Loại Trừ
          </button>
        `;
      } else {
        actionButtons = `
          <button class="btn btn-outline w-100" onclick="showProductDetails(${prd.id})">
            <i class="bi bi-file-text"></i> Xem Quy Tắc & Điều Khoản
          </button>
        `;
      }

      // Lấy danh sách 3 quyền lợi cốt lõi theo từng gói sản phẩm
      const code = prd.product_code || "PRD-HLT-01";
      const prdInfo = PRODUCT_DETAILS_KNOWLEDGE[code] || PRODUCT_DETAILS_KNOWLEDGE["PRD-HLT-01"];
      const highlights = prdInfo.benefits.slice(0, 3);

      card.innerHTML = `
        <span class="product-badge">${prd.category}</span>
        <h4>${prd.product_name}</h4>
        <p>${prd.description || ''}</p>

        <div class="product-meta-row">
          <span class="text-muted">Hạn mức chi trả tối đa:</span>
          <strong class="text-success">${formatNumberWithDots(prd.max_coverage_limit)} VNĐ</strong>
        </div>

        <!-- BẢNG TÓM TẮT QUYỀN LỢI CỐT LÕI -->
        <div class="card-benefits-preview">
          ${highlights.map(h => `
            <div class="benefit-preview-item">
              <i class="bi bi-shield-check"></i>
              <span><strong>${h.title}:</strong> ${h.limit}</span>
            </div>
          `).join("")}
        </div>

        <!-- BẢNG BIỂU PHÍ THEO KỲ THANH TOÁN -->
        <div class="card-pricing-cycles">
          <div class="cycle-pill-box">
            <span class="cycle-label">Năm (Tiết kiệm)</span>
            <span class="cycle-val">${formatNumberWithDots(prd.base_annual_premium)} đ</span>
          </div>
          <div class="cycle-pill-box">
            <span class="cycle-label">Quý (3 tháng)</span>
            <span class="cycle-val">${formatNumberWithDots(Math.round(prd.base_annual_premium * 0.27))} đ</span>
          </div>
          <div class="cycle-pill-box">
            <span class="cycle-label">Tháng</span>
            <span class="cycle-val">${formatNumberWithDots(Math.round(prd.base_annual_premium * 0.095))} đ</span>
          </div>
        </div>

        <div class="mt-2">
          ${actionButtons}
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error(err);
  }
}

function openBuyProduct(productId) {
  openCreatePolicyModal();
  setTimeout(() => {
    const pSelect = document.getElementById("policyProductSelect");
    if (pSelect) {
      pSelect.value = productId;
      onPolicyProductSelected();
    }
  }, 350);
}

function openAgentIssueForProduct(productId) {
  openCreatePolicyModal();
  setTimeout(() => {
    const pSelect = document.getElementById("policyProductSelect");
    if (pSelect) {
      pSelect.value = productId;
      onPolicyProductSelected();
    }
  }, 350);
}

// KHO DỮ LIỆU ĐIỀU KHOẢN, QUYỀN LỢI & ĐIỂM LOẠI TRỪ CHI TIẾT
const PRODUCT_DETAILS_KNOWLEDGE = {
  "PRD-HLT-01": {
    benefits: [
      { title: "Viện phí điều trị nội trú thực tế", desc: "Thanh toán 100% chi phí y tế phát sinh hợp lý thuộc danh mục điều trị theo chỉ định của bác sĩ tại các bệnh viện công lập và tư nhân hợp pháp.", limit: "Tối đa 50.000.000 VNĐ / năm" },
      { title: "Chi phí phẫu thuật điều trị nội trú", desc: "Bao gồm chi phí phẫu thuật viên, phòng mổ, gây mê, hồi sức sau mổ, thuốc men và vật tư y tế tiêu hao trong ca mổ.", limit: "Lên tới 30.000.000 VNĐ / ca" },
      { title: "Tiền phòng và giường bệnh tiêu chuẩn", desc: "Chi trả tiền phòng điều trị nội trú tại bệnh viện đạt chuẩn trên toàn quốc (tối đa 60 ngày nằm viện / năm).", limit: "Tối đa 1.500.000 VNĐ / ngày" },
      { title: "Khoa chăm sóc đặc biệt (ICU/CCU)", desc: "Chi phí nằm phòng hồi sức tích cực khi có chỉ định bác sĩ chuyên khoa do diễn biến bệnh nguy kịch.", limit: "Tối đa 3.000.000 VNĐ / ngày" },
      { title: "Trợ cấp mai táng do tai nạn", desc: "Hỗ trợ tài chính tức thì cho gia đình người được bảo hiểm nếu xảy ra biến cố trong thời hạn hợp đồng.", limit: "5.000.000 VNĐ" }
    ],
    waiting: [
      { badgeClass: "badge-zero", badgeText: "0 Ngày", title: "Tai nạn giao thông & sinh hoạt", desc: "Hiệu lực bảo vệ kích hoạt tức thì ngay sau khi hợp đồng được phê duyệt và đóng phí hợp lệ." },
      { badgeClass: "badge-30", badgeText: "30 Ngày", title: "Bệnh thông thường & phẫu thuật cấp tính", desc: "Áp dụng cho các bệnh lý ốm đau thông thường như sốt xuất huyết, viêm phế quản, mổ ruột thừa..." },
      { badgeClass: "badge-90", badgeText: "180 Ngày", title: "Bệnh hô hấp, tai mũi họng & tiểu phẫu", desc: "Áp dụng cho phẫu thuật nạo VA, cắt amidan, viêm xoang mạn tính, sỏi hệ tiết niệu..." },
      { badgeClass: "badge-365", badgeText: "365 Ngày", title: "Bệnh đặc biệt & bệnh có sẵn được chấp thuận", desc: "Bệnh đặc biệt theo danh mục Bộ Y Tế, bệnh có sẵn đã kê khai được bảo hiểm chấp thuận và thai sản." }
    ],
    exclusions: [
      { title: "Phẫu thuật & Điều trị thẩm mỹ", desc: "Phẫu thuật thẩm mỹ, chỉnh hình (nâng mũi, hút mỡ, độn cằm, cắt mí...), nha khoa thẩm mỹ (trừ khi do tai nạn ngoại lực cần tái tạo chức năng giải phẫu)." },
      { title: "Bệnh có sẵn không khai báo trung thực", desc: "Mọi bệnh tật hoặc thương tật đã tồn tại trước ngày hiệu lực hợp đồng mà bên mua bảo hiểm không kê khai đầy đủ, trung thực." },
      { title: "Khám sức khỏe định kỳ & Tầm soát tự nguyện", desc: "Chi phí kiểm tra sức khỏe tổng quát, tầm soát không có triệu chứng bệnh, điều trị suy nhược cơ thể, mất ngủ, béo phì." },
      { title: "Vi phạm nồng độ cồn & Chất kích thích cấm", desc: "Điều khiển phương tiện giao thông khi nồng độ cồn trong máu/hơi thở vượt ngưỡng cho phép hoặc sử dụng ma túy, chất gây nghiện trái phép." }
    ],
    claimDocs: [
      { icon: "bi-file-earmark-medical", title: "Giấy ra viện / Trích sao bệnh án", desc: "Bản gốc hoặc trích lục có đóng dấu mộc đỏ tròn của bệnh viện điều trị" },
      { icon: "bi-receipt-cutoff", title: "Bảng kê chi tiết viện phí (Mẫu 01/BV)", desc: "Liệt kê rõ từng khoản mục tiền thuốc, tiền phòng, dịch vụ kỹ thuật" },
      { icon: "bi-cash-coin", title: "Hóa đơn điện tử viện phí", desc: "Hóa đơn tài chính hợp pháp có mã của cơ quan thuế" },
      { icon: "bi-prescription2", title: "Toa thuốc xuất viện & Phiếu kết quả", desc: "Kèm phim X-quang, MRI, CT hoặc phiếu xét nghiệm máu liên quan" }
    ]
  },
  "PRD-ACC-02": {
    benefits: [
      { title: "Tử vong do tai nạn 24/7", desc: "Chi trả toàn bộ 100% quyền lợi bảo hiểm khi người được bảo hiểm tử vong do tai nạn trong phạm vi bảo hiểm.", limit: "100.000.000 VNĐ (100%)" },
      { title: "Thương tật toàn bộ vĩnh viễn", desc: "Mất hoặc liệt hoàn toàn hai chi, mù hai mắt hoặc mất khả năng lao động trên 81% vĩnh viễn do tai nạn.", limit: "100.000.000 VNĐ (100%)" },
      { title: "Thương tật bộ phận vĩnh viễn", desc: "Chi trả theo Bảng tỷ lệ thương tật chuẩn của Bộ Tài Chính (ví dụ: gãy xương 15-25%, mất ngón 10-20%).", limit: "Tỷ lệ % x 100.000.000 VNĐ" },
      { title: "Chi phí y tế cấp cứu & điều trị tai nạn", desc: "Chi trả toàn bộ viện phí cấp cứu, phẫu thuật kết hợp xương, thuốc men phát sinh thực tế do tai nạn.", limit: "Tối đa 20.000.000 VNĐ / vụ" },
      { title: "Trợ cấp thu nhập nằm viện tai nạn", desc: "Hỗ trợ tài chính bù đắp thu nhập gián đoạn trong những ngày điều trị nội trú chấn thương (tối đa 90 ngày).", limit: "150.000 VNĐ / ngày" }
    ],
    waiting: [
      { badgeClass: "badge-zero", badgeText: "0 Ngày", title: "Rủi ro tai nạn giao thông 24/7", desc: "Bảo vệ ngay lập tức khi tham gia giao thông bằng ô tô, xe máy, xe buýt hợp pháp trên toàn quốc." },
      { badgeClass: "badge-zero", badgeText: "0 Ngày", title: "Rủi ro tai nạn sinh hoạt & lao động", desc: "Bảo vệ ngay lập tức trước các sự cố trượt ngã, bỏng, chấn thương trong sinh hoạt và làm việc hàng ngày." }
    ],
    exclusions: [
      { title: "Vi phạm luật giao thông & Nồng độ cồn", desc: "Người điều khiển phương tiện tham gia giao thông có nồng độ cồn vượt quy định hoặc sử dụng chất ma túy, chất kích thích cấm." },
      { title: "Thể thao mạo hiểm không mua quyền lợi mở rộng", desc: "Tham gia đua xe, nhảy dù, lặn biển bình dưỡng khí, leo núi chuyên nghiệp, thi đấu thể thao đối kháng chuyên nghiệp." },
      { title: "Hành vi cố ý vi phạm pháp luật hình sự", desc: "Cố ý gây án tích, tham gia đánh nhau (trừ trường hợp phòng vệ chính đáng), chống người thi hành công vụ." },
      { title: "Đột quỵ, tai biến & bệnh lý nội khoa", desc: "Nhồi máu cơ tim, đột quỵ não, ngộ độc thực phẩm... (xem là bệnh lý, không thuộc định nghĩa tai nạn ngoại lực tác động)." }
    ],
    claimDocs: [
      { icon: "bi-shield-shaded", title: "Biên bản tai nạn / Kết luận Công an", desc: "Đối với tai nạn giao thông hoặc tai nạn lao động nghiêm trọng cần hồ sơ công an" },
      { icon: "bi-hospital", title: "Giấy chứng nhận thương tích / Bệnh án cấp cứu", desc: "Ghi nhận rõ cơ chế chấn thương ngoại lực và chẩn đoán ban đầu" },
      { icon: "bi-receipt", title: "Hóa đơn tài chính & Bảng kê phẫu thuật", desc: "Hóa đơn điện tử viện phí, tiền đinh nẹp, vật tư kết hợp xương tiêu hao" },
      { icon: "bi-person-badge", title: "Giấy giám định tỷ lệ thương tật", desc: "Do Hội đồng Giám định Y khoa cấp tỉnh cấp (nếu yêu cầu chi trả thương tật vĩnh viễn)" }
    ]
  },
  "PRD-MED-03": {
    benefits: [
      { title: "Bệnh hiểm nghèo giai đoạn đầu", desc: "Chi trả trước 25% hạn mức để người bệnh kịp thời tiếp cận các phác đồ điều trị chuyên sâu và công nghệ tiên tiến nhất.", limit: "50.000.000 VNĐ (25%)" },
      { title: "Bệnh hiểm nghèo giai đoạn sau", desc: "Chi trả toàn bộ 100% hạn mức khi xác định mắc một trong 45 danh mục bệnh hiểm nghèo chuẩn Bộ Y Tế.", limit: "200.000.000 VNĐ (100%)" },
      { title: "Trợ cấp phục hồi sau đại phẫu bệnh lý", desc: "Hỗ trợ chi phí dinh dưỡng bồi bổ và vật lý trị liệu phục hồi chức năng sau các ca phẫu thuật bệnh lý nghiêm trọng.", limit: "10.000.000 VNĐ" },
      { title: "Miễn đóng toàn bộ phí bảo hiểm còn lại", desc: "Người tham gia được miễn nộp toàn bộ các kỳ phí bảo hiểm còn lại của hợp đồng khi mắc bệnh giai đoạn sau.", limit: "Miễn nộp 100% phí" }
    ],
    waiting: [
      { badgeClass: "badge-90", badgeText: "90 Ngày", title: "Thời gian chờ tiêu chuẩn bệnh hiểm nghèo", desc: "Bệnh hiểm nghèo phải phát sinh triệu chứng hoặc được chẩn đoán sau 90 ngày kể từ ngày hợp đồng có hiệu lực." },
      { badgeClass: "badge-30", badgeText: "14 Ngày", title: "Thời gian sống sót tối thiểu", desc: "Người được bảo hiểm phải còn sống tối thiểu 14 ngày kể từ ngày có kết luận chẩn đoán xác định mắc bệnh." }
    ],
    exclusions: [
      { title: "Bệnh phát sinh trong 90 ngày thời gian chờ", desc: "Bất kỳ dấu hiệu, triệu chứng hoặc kết luận chẩn đoán bệnh xuất hiện trong vòng 90 ngày đầu tiên của hợp đồng." },
      { title: "Bệnh bẩm sinh & Khiếm khuyết di truyền", desc: "Dị tật bẩm sinh, bệnh tim bẩm sinh hoặc khiếm khuyết di truyền đã tồn tại từ trước khi tham gia bảo hiểm." },
      { title: "Hội chứng suy giảm miễn dịch HIV/AIDS", desc: "Ngoại trừ trường hợp lây nhiễm do truyền máu nghề nghiệp y tế hoặc nạn nhân bị tấn công khi thi hành công vụ." },
      { title: "Tự đầu độc & Lạm dụng dược phẩm", desc: "Cố ý sử dụng độc chất, dùng thuốc quá liều hoặc dùng dược phẩm không theo đơn chỉ định của bác sĩ chuyên khoa." }
    ],
    claimDocs: [
      { icon: "bi-file-earmark-medical", title: "Kết quả giải phẫu bệnh lý (Sinh thiết)", desc: "Bắt buộc có đối với bệnh ung thư / u ác tính (có chữ ký bác sĩ giải phẫu bệnh)" },
      { icon: "bi-file-earmark-ruled", title: "Tóm tắt hồ sơ bệnh án & Giấy xuất viện", desc: "Do Bệnh viện chuyên khoa tuyến tỉnh/trung ương kết luận và đóng dấu mộc" },
      { icon: "bi-activity", title: "Kết quả cận lâm sàng chuyên sâu", desc: "Phim chụp MRI, CT Scanner, Xạ hình xương, Điện tim, Siêu âm tim, Đo tủy đồ..." },
      { icon: "bi-person-check", title: "Đơn yêu cầu giải quyết bồi thường", desc: "Kèm CCCD người thụ hưởng và xác nhận còn sống sau 14 ngày" }
    ]
  }
};

let currentTermsProductId = null;

// HIỂN THỊ MODAL QUY TẮC ĐIỀU KHOẢN & ĐIỂM LOẠI TRỪ CHI TIẾT
function showProductDetails(productId) {
  const modal = document.getElementById("productTermsModal");
  if (!modal) return;

  let foundPrd = null;
  if (typeof productId === "number") {
    foundPrd = cachedProductsList.find(p => p.id === productId);
  }
  if (!foundPrd) {
    foundPrd = cachedProductsList[0] || {
      id: 1,
      product_code: "PRD-HLT-01",
      product_name: "Bảo hiểm Sức khỏe Phúc An Toàn diện",
      category: "Sức khỏe",
      description: "Bảo vệ toàn diện trước rủi ro ốm đau, viện phí và phẫu thuật.",
      max_coverage_limit: 50000000,
      base_annual_premium: 3500000
    };
  }

  currentTermsProductId = foundPrd.id;

  // Điền thông tin Tiêu đề Header
  document.getElementById("termsProductName").textContent = foundPrd.product_name;
  document.getElementById("termsProductDesc").textContent = foundPrd.description || "Quy tắc điều khoản bồi thường và danh mục quyền lợi chi tiết theo chuẩn Bộ Tài Chính.";
  document.getElementById("termsCategoryBadge").textContent = foundPrd.category || "Bảo hiểm";
  document.getElementById("termsMaxLimit").textContent = formatVND(foundPrd.max_coverage_limit);
  document.getElementById("termsAnnualPremium").textContent = `${formatVND(foundPrd.base_annual_premium)} / năm`;

  // Trích xuất kho tri thức chi tiết theo mã gói (hoặc mặc định)
  const code = foundPrd.product_code || "PRD-HLT-01";
  const data = PRODUCT_DETAILS_KNOWLEDGE[code] || PRODUCT_DETAILS_KNOWLEDGE["PRD-HLT-01"];

  // 1. Tab Quyền Lợi
  const benBox = document.getElementById("termsBenefitsContent");
  benBox.innerHTML = data.benefits.map(b => `
    <div class="terms-benefit-row">
      <div class="benefit-desc">
        <strong><i class="bi bi-shield-check text-success"></i> ${b.title}</strong>
        <small>${b.desc}</small>
      </div>
      <div class="benefit-limit-tag">${b.limit}</div>
    </div>
  `).join("");

  // 2. Tab Biểu Phí Định Kỳ & Chiết Khấu
  const pricingBox = document.getElementById("termsPricingContent");
  if (pricingBox) {
    pricingBox.innerHTML = `
      <table class="terms-pricing-table">
        <thead>
          <tr>
            <th>Kỳ Nộp Phí</th>
            <th>Số Tiền Mỗi Kỳ</th>
            <th>Tổng Phí Quy Đổi / Năm</th>
            <th>Chính Sách Ưu Đãi</th>
          </tr>
        </thead>
        <tbody>
          <tr class="highlight-annual">
            <td><strong><i class="bi bi-star-fill text-warning"></i> Hàng Năm (Thường Niên)</strong></td>
            <td><strong class="text-success">${formatNumberWithDots(foundPrd.base_annual_premium)} VNĐ</strong></td>
            <td>${formatNumberWithDots(foundPrd.base_annual_premium)} VNĐ</td>
            <td><span class="discount-tag">Tiết kiệm 15%</span> (Khuyên dùng)</td>
          </tr>
          <tr>
            <td><strong>Hàng Quý (3 tháng / kỳ)</strong></td>
            <td><strong class="text-success">${formatNumberWithDots(Math.round(foundPrd.base_annual_premium * 0.27))} VNĐ</strong></td>
            <td>${formatNumberWithDots(Math.round(foundPrd.base_annual_premium * 1.08))} VNĐ</td>
            <td>Linh hoạt dòng tiền 4 kỳ/năm</td>
          </tr>
          <tr>
            <td><strong>Hàng Tháng</strong></td>
            <td><strong class="text-success">${formatNumberWithDots(Math.round(foundPrd.base_annual_premium * 0.095))} VNĐ</strong></td>
            <td>${formatNumberWithDots(Math.round(foundPrd.base_annual_premium * 1.14))} VNĐ</td>
            <td>Đóng phí nhẹ nhàng hàng tháng</td>
          </tr>
        </tbody>
      </table>

      <div class="terms-section-title mt-3">
        <i class="bi bi-people-fill text-primary"></i> Biểu phí tiêu chuẩn theo nhóm tuổi tham gia (Đóng thường niên)
      </div>
      <table class="terms-pricing-table">
        <thead>
          <tr>
            <th>Nhóm Tuổi Người Tham Gia</th>
            <th>Mức Phí Chuẩn / Năm</th>
            <th>Hạn Mức Quyền Lợi</th>
            <th>Ghi Chú Nghiệp Vụ</th>
          </tr>
        </thead>
        <tbody>
          ${(data.ageRates || [
            { age: "0 - 18 tuổi", fee: Math.round(foundPrd.base_annual_premium * 0.8), note: "Trẻ em & Học sinh sinh viên" },
            { age: "19 - 35 tuổi (Chuẩn)", fee: foundPrd.base_annual_premium, note: "Độ tuổi lao động tiêu chuẩn" },
            { age: "36 - 50 tuổi", fee: Math.round(foundPrd.base_annual_premium * 1.3), note: "Gia tăng bảo vệ bệnh lý" },
            { age: "51 - 65 tuổi", fee: Math.round(foundPrd.base_annual_premium * 1.75), note: "Tái tục đến 65 tuổi" }
          ]).map(a => `
            <tr>
              <td><strong>${a.age}</strong></td>
              <td><strong class="text-success">${formatNumberWithDots(a.fee)} VNĐ</strong></td>
              <td>${formatNumberWithDots(foundPrd.max_coverage_limit)} VNĐ</td>
              <td>${a.note}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  // 3. Tab Thời Gian Chờ
  const waitBox = document.getElementById("termsWaitingContent");
  waitBox.innerHTML = `
    <div class="waiting-timeline">
      ${data.waiting.map(w => `
        <div class="waiting-item">
          <div class="waiting-badge ${w.badgeClass}">${w.badgeText}</div>
          <div>
            <strong>${w.title}</strong>
            <p class="text-muted mb-0" style="font-size: 12.5px; line-height: 1.4;">${w.desc}</p>
          </div>
        </div>
      `).join("")}
    </div>
  `;

  // 3. Tab Điểm Loại Trừ
  const exclBox = document.getElementById("termsExclusionsContent");
  exclBox.innerHTML = data.exclusions.map(e => `
    <div class="exclusion-alert-card">
      <strong><i class="bi bi-slash-circle-fill"></i> ${e.title}</strong>
      <p>${e.desc}</p>
    </div>
  `).join("");

  // 4. Tab Hồ Sơ Bồi Thường
  const docsBox = document.getElementById("termsClaimDocsContent");
  docsBox.innerHTML = `
    <div class="doc-checklist">
      ${data.claimDocs.map(d => `
        <div class="doc-item">
          <i class="bi ${d.icon}"></i>
          <div>
            <strong>${d.title}</strong>
            <small class="text-muted d-block">${d.desc}</small>
          </div>
        </div>
      `).join("")}
    </div>
  `;

  // Thiết lập nút hành động phù hợp vai trò
  const btnAction = document.getElementById("btnModalActionForProduct");
  if (btnAction) {
    if (currentUser && currentUser.role === "customer") {
      btnAction.style.display = "inline-flex";
      btnAction.innerHTML = `<i class="bi bi-cart-plus-fill"></i> Đăng Ký Mua Gói Này`;
    } else if (currentUser && currentUser.role === "agent") {
      btnAction.style.display = "inline-flex";
      btnAction.innerHTML = `<i class="bi bi-person-plus-fill"></i> Cấp Hợp Đồng Cho Khách`;
    } else if (currentUser && currentUser.role === "admin") {
      btnAction.style.display = "inline-flex";
      btnAction.innerHTML = `<i class="bi bi-journal-plus"></i> Phát Hành Hợp Đồng`;
    } else {
      btnAction.style.display = "none";
    }
  }

  // Mặc định mở Tab 1: Quyền Lợi
  switchTermsTab('benefits');

  modal.style.display = "flex";
}

// Chuyển Tab bên trong Modal Quy Tắc Điều Khoản
function switchTermsTab(tabKey) {
  document.querySelectorAll(".terms-tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".terms-pane").forEach(p => p.classList.remove("active"));

  const targetBtn = document.getElementById(`tabBtn_${tabKey}`);
  const targetPane = document.getElementById(`termsPane_${tabKey}`);

  if (targetBtn) targetBtn.classList.add("active");
  if (targetPane) targetPane.classList.add("active");
}

// Đóng Modal Quy Tắc Điều Khoản
function closeProductTermsModal() {
  const modal = document.getElementById("productTermsModal");
  if (modal) modal.style.display = "none";
}

// Xử lý nút hành động trên Modal (Mua hoặc Cấp)
function handleTermsModalAction() {
  if (!currentTermsProductId) return;
  const pId = currentTermsProductId;
  closeProductTermsModal();
  if (currentUser && currentUser.role === "customer") {
    openBuyProduct(pId);
  } else {
    openAgentIssueForProduct(pId);
  }
}

// Hỏi Trợ lý AI Advisor về gói sản phẩm đang xem
function askAiAboutThisProduct() {
  const prdName = document.getElementById("termsProductName").textContent;
  closeProductTermsModal();
  switchTab("chatbot");
  const input = document.getElementById("chatInputText");
  if (input) {
    input.value = `Tư vấn chi tiết về quyền lợi, thời gian chờ và điểm loại trừ của gói ${prdName}?`;
    sendChatMessage();
  }
}

// 6. THU PHÍ ĐỊNH KỲ
async function loadPayments() {
  try {
    const res = await fetch(`${API_BASE}/finance/payments`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    const payments = await res.json();
    const tbody = document.getElementById("paymentsTableBody");
    tbody.innerHTML = "";

    if (payments.length === 0) {
      const msg = currentUser.role === "customer" 
        ? "Bạn chưa có kỳ nộp phí nào cần thanh toán."
        : "Chưa có giao dịch thu phí nào trong hệ thống.";
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">${msg}</td></tr>`;
      return;
    }

    payments.forEach(pay => {
      const tr = document.createElement("tr");
      const methodMap = {
        BANK_TRANSFER: "Chuyển khoản NH",
        MOMO: "Ví MoMo",
        VNPAY: "Cổng VNPAY",
        CASH: "Tiền mặt"
      };
      const methodName = methodMap[pay.payment_method] || pay.payment_method || "Chuyển khoản";
      const polNum = pay.policy_number || (`POL-${pay.policy_id.toString().padStart(3, '0')}`);
      const custInfo = pay.customer_name ? `<br><small class="text-muted"><i class="bi bi-person"></i> ${pay.customer_name}</small>` : '';

      tr.innerHTML = `
        <td><strong class="text-success">${pay.payment_code}</strong></td>
        <td><strong class="text-primary">${polNum}</strong>${custInfo}</td>
        <td>${pay.period_name}</td>
        <td><strong class="text-success">${formatVND(pay.amount)}</strong></td>
        <td><span class="badge badge-info">${methodName}</span></td>
        <td>${new Date(pay.payment_date).toLocaleDateString('vi-VN')}</td>
        <td><span class="status-pill status-approved">Đã thanh toán</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error(err);
  }
}

// 7. TRỢ LÝ AI ADVISOR CHATBOT

// Định dạng văn bản phản hồi của Chatbot thành HTML trực quan
function formatChatbotText(text) {
  if (!text) return "";
  let html = text
    // Đổi định dạng in đậm **text** -> <strong>text</strong>
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Đổi gạch đầu dòng • -> bullet point đẹp
    .replace(/^•\s+(.*)$/gm, '<li class="chat-bullet-item">$1</li>')
    .replace(/^-\s+(.*)$/gm, '<li class="chat-bullet-item">$1</li>')
    // Đổi các tiêu đề đánh số 1., 2., 3.
    .replace(/^([0-9]+\.\s+.*)$/gm, '<div class="chat-section-header"><strong>$1</strong></div>');

  // Bọc các <li> liên tiếp trong <ul>
  html = html.replace(/(<li class="chat-bullet-item">.*?<\/li>)+/gs, '<ul class="chat-bullet-list">$&</ul>');
  // Chuyển ngắt dòng \n thành ngắt đoạn
  html = html.replace(/\n\n/g, '<div class="my-2"></div>');
  return html;
}

// Bộ câu hỏi mẫu theo chuyên đề phong phú
const CHAT_TOPIC_PRESETS = {
  all: [
    { label: "Phẫu thuật thẩm mỹ có được chi trả?", prompt: "Gói bảo hiểm sức khỏe có chi trả phẫu thuật thẩm mỹ không?" },
    { label: "Thời gian chờ bệnh hiểm nghèo?", prompt: "Thời gian chờ của gói bảo hiểm bệnh hiểm nghèo là bao lâu?" },
    { label: "Gợi ý gói bảo hiểm tuổi 32?", prompt: "Tôi 32 tuổi làm văn phòng nên chọn gói bảo hiểm nào?" },
    { label: "Hồ sơ bồi thường cần giấy tờ gì?", prompt: "Hồ sơ yêu cầu bồi thường bảo hiểm gồm những chứng từ gì?" },
    { label: "Gãy xương do tai nạn bồi thường thế nào?", prompt: "Gãy xương do tai nạn ngã tại nhà có được chi trả viện phí không?" },
    { label: "Hạn mức viện phí & phẫu thuật nội trú?", prompt: "Hạn mức tiền giường nội trú và tiền phẫu thuật được thanh toán bao nhiêu?" }
  ],
  hospital: [
    { label: "Mổ ruột thừa viện phí bao nhiêu?", prompt: "Chi phí mổ ruột thừa nằm viện 3 ngày được thanh toán bao nhiêu tiền?" },
    { label: "Nằm viện Vinmec / FV có được trả?", prompt: "Nằm viện tại bệnh viện quốc tế như Vinmec hoặc FV có được thanh toán không?" },
    { label: "Hạn mức tiền giường phòng dịch vụ?", prompt: "Tiền giường phòng dịch vụ tối đa được thanh toán bao nhiêu tiền một ngày?" },
    { label: "Khám ngoại trú trong ngày có được trả?", prompt: "Điều trị khám ngoại trú trong ngày có được bồi thường không?" }
  ],
  waiting: [
    { label: "Thời gian chờ bệnh hiểm nghèo?", prompt: "Thời gian chờ đối với bệnh hiểm nghèo ung thư là bao lâu?" },
    { label: "Thời gian chờ bệnh thông thường & tai nạn?", prompt: "Thời gian chờ đối với bệnh thông thường và tai nạn là mấy ngày?" },
    { label: "Bệnh đặc biệt như sỏi thận, trĩ?", prompt: "Bệnh đặc biệt như sỏi thận, trĩ, thoát vị đĩa đệm phải chờ bao nhiêu ngày?" },
    { label: "Thai sản sinh con chờ bao lâu?", prompt: "Thời gian chờ của quyền lợi thai sản sinh đẻ là bao nhiêu ngày?" }
  ],
  accident: [
    { label: "Gãy tay ngã xe đền bao nhiêu?", prompt: "Gãy tay bó bột do ngã xe máy được bồi thường bao nhiêu tiền?" },
    { label: "Tai nạn có thời gian chờ không?", prompt: "Bảo hiểm tai nạn thương tích có áp dụng thời gian chờ không?" },
    { label: "Trợ cấp nằm viện do tai nạn?", prompt: "Trợ cấp ngày nằm viện do tai nạn được bao nhiêu tiền một ngày?" },
    { label: "Nồng độ cồn khi tai nạn có được đền?", prompt: "Nếu xảy ra tai nạn khi có nồng độ cồn thì có được bồi thường không?" }
  ],
  critical: [
    { label: "Ung thư giai đoạn đầu có được tiền mặt?", prompt: "Bị ung thư giai đoạn đầu có được thanh toán tiền mặt 1 lần không?" },
    { label: "Chi phí hóa trị xạ trị có được trả?", prompt: "Chi phí hóa trị, xạ trị ung thư có được bảo hiểm chi trả không?" },
    { label: "Hạn mức gói Bệnh Hiểm Nghèo?", prompt: "Hạn mức tối đa của gói Bảo hiểm Bệnh Hiểm Nghèo Vững Tâm là bao nhiêu?" },
    { label: "Điều kiện sống sót 30 ngày là gì?", prompt: "Tại sao bệnh hiểm nghèo lại có điều kiện người bệnh phải còn sống 30 ngày?" }
  ],
  claim: [
    { label: "Hồ sơ claim bồi thường cần giấy tờ gì?", prompt: "Hồ sơ yêu cầu bồi thường bảo hiểm gồm những chứng từ gì?" },
    { label: "Thời hạn nộp claim sau khi ra viện?", prompt: "Thời hạn nộp hồ sơ yêu cầu bồi thường sau khi xuất viện là bao lâu?" },
    { label: "Bao lâu thì nhận được tiền claim?", prompt: "Sau bao lâu kể từ khi nộp claim thì tôi nhận được tiền chuyển khoản?" },
    { label: "Bị từ chối claim thì khiếu nại ở đâu?", prompt: "Nếu hồ sơ bồi thường bị từ chối thì tôi có quyền khiếu nại ở đâu?" }
  ],
  advice: [
    { label: "Gợi ý gói tuổi 25 độc thân?", prompt: "Tôi 25 tuổi mới đi làm thì nên chọn gói bảo hiểm nào tiết kiệm nhất?" },
    { label: "Gợi ý gói tuổi 35 trụ cột gia đình?", prompt: "Tôi 35 tuổi là trụ cột chính trong nhà nên mua gói bảo vệ nào?" },
    { label: "Người trên 50 tuổi nên mua gói nào?", prompt: "Bố mẹ tôi 52 tuổi thì nên tham gia gói bảo hiểm nào tối ưu?" },
    { label: "Làm công nhân xây dựng nên mua gói gì?", prompt: "Tôi làm việc tại công trường xây dựng nên chọn gói bảo hiểm tai nạn nào?" }
  ],
  family: [
    { label: "Sinh mổ tại viện phụ sản đền bao nhiêu?", prompt: "Sinh mổ tại bệnh viện phụ sản được bảo hiểm thanh toán tối đa bao nhiêu?" },
    { label: "Bé 2 tuổi hay ốm hô hấp mua gói gì?", prompt: "Bé 2 tuổi hay bị viêm phế quản phổi và sốt cao thì nên mua gói bảo hiểm nào?" },
    { label: "Khám thai định kỳ có được thanh toán?", prompt: "Bảo hiểm thai sản có chi trả các đợt khám thai định kỳ không?" },
    { label: "Gói bảo hiểm cho cả gia đình?", prompt: "Có gói bảo hiểm nào dành cho cả gia đình gồm bố mẹ và con nhỏ không?" }
  ],
  dental: [
    { label: "Nhổ răng khôn mọc lệch có được trả?", prompt: "Nhổ răng khôn mọc lệch mọc ngầm có được bảo hiểm y tế chi trả không?" },
    { label: "Mổ cận thị Lasik có được trả?", prompt: "Phẫu thuật mổ mắt cận thị Lasik có nằm trong danh mục chi trả không?" },
    { label: "Chữa tủy và trám răng sâu?", prompt: "Chữa tủy và trám răng sâu bệnh lý có được bồi thường viện phí không?" },
    { label: "Mổ đục thủy tinh thể Phaco?", prompt: "Mổ mắt đục thủy tinh thể Phaco có được thanh toán viện phí không?" }
  ],
  rule: [
    { label: "Những điểm loại trừ không chi trả?", prompt: "Những trường hợp nào thuộc điểm loại trừ không được bảo hiểm bồi thường?" },
    { label: "Bệnh có sẵn có được chi trả không?", prompt: "Bệnh có sẵn trước khi mua bảo hiểm có được bồi thường không?" },
    { label: "Có 2 bảo hiểm có được trả gấp đôi?", prompt: "Mua cùng lúc 2 bảo hiểm ở 2 công ty có được thanh toán viện phí gấp đôi không?" },
    { label: "Rút tiền hủy hợp đồng có mất phí?", prompt: "Hủy hợp đồng bảo hiểm sức khỏe trước hạn có được lấy lại tiền không?" }
  ]
};

// Chuyển đổi tab chủ đề câu hỏi mẫu
function switchChatTopic(topicKey, btnElement) {
  document.querySelectorAll(".topic-pill").forEach(p => p.classList.remove("active"));
  if (btnElement) btnElement.classList.add("active");

  const container = document.getElementById("activeQuickSuggests");
  if (!container) return;

  const presets = CHAT_TOPIC_PRESETS[topicKey] || CHAT_TOPIC_PRESETS.all;
  container.innerHTML = "";
  presets.forEach(item => {
    const btn = document.createElement("button");
    btn.className = "suggest-btn";
    btn.textContent = item.label;
    btn.onclick = () => sendQuickPrompt(item.prompt);
    container.appendChild(btn);
  });
}

// Bắt đầu lại cuộc hội thoại mới
function resetChatHistory() {
  const messagesBox = document.getElementById("chatMessages");
  if (!messagesBox) return;

  messagesBox.innerHTML = `
    <div class="message message-bot">
      <div class="message-bubble">
        <p>Kính chào Quý khách! Tôi là <strong>Trợ lý Ảo InsurTech Smart Advisor</strong> - Chuyên gia Tư vấn Nghiệp vụ Bảo hiểm Thông minh 24/7. Tôi có thể hỗ trợ giải đáp chuẩn xác mọi quy tắc quyền lợi, thời gian chờ, hạn mức viện phí và thủ tục bồi thường. Quý khách muốn tìm hiểu nội dung gì hôm nay?</p>
        <div class="quick-suggests" id="activeQuickSuggests"></div>
      </div>
    </div>
  `;

  switchChatTopic('all', document.querySelector('.topic-pill'));
  showToast("Đã khởi tạo phiên tư vấn bảo hiểm mới!");
}

// Mở Modal Xem Chứng Nhận Bảo Mật PII & Kiểm Soát An Toàn
function showPiiSecurityInfo() {
  const modal = document.getElementById("piiSecurityModal");
  if (modal) {
    modal.style.display = "flex";
  } else {
    showToast("🛡️ Đã bảo mật PII: Dữ liệu cá nhân (CCCD, SĐT, Viện phí) được che mờ tự động trước khi phân tích AI.", "info");
  }
}

function closePiiSecurityModal() {
  const modal = document.getElementById("piiSecurityModal");
  if (modal) {
    modal.style.display = "none";
  }
}

async function sendChatMessage() {
  const input = document.getElementById("chatInputText");
  const msg = input.value.trim();
  if (!msg) return;

  const messagesBox = document.getElementById("chatMessages");

  // 1. Render tin nhắn của User
  const userDiv = document.createElement("div");
  userDiv.className = "message message-user";
  userDiv.innerHTML = `<div class="message-bubble"><p>${msg.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</p></div>`;
  messagesBox.appendChild(userDiv);
  input.value = "";
  messagesBox.scrollTop = messagesBox.scrollHeight;

  // 2. Render tin nhắn chờ của Bot
  const botDiv = document.createElement("div");
  botDiv.className = "message message-bot";
  botDiv.innerHTML = `<div class="message-bubble"><p><i class="bi bi-hourglass-split"></i> Chuyên gia InsurTech đang đối soát quy tắc điều khoản & phân tích câu hỏi...</p></div>`;
  messagesBox.appendChild(botDiv);
  messagesBox.scrollTop = messagesBox.scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/ai/chat-advisor`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({ message: msg })
    });

    if (!res.ok) {
      throw new Error("Lỗi kết nối máy chủ tư vấn AI.");
    }

    const data = await res.json();
    const formattedReply = formatChatbotText(data.reply);

    // Xây dựng danh sách câu hỏi gợi ý tiếp theo
    let suggestsHtml = "";
    if (data.suggested_questions && data.suggested_questions.length > 0) {
      suggestsHtml = `
        <div class="mt-3 pt-2" style="border-top: 1px dashed #cbd5e1;">
          <small class="text-muted fw-bold"><i class="bi bi-lightbulb-fill text-warning"></i> Câu hỏi liên quan Quý khách có thể quan tâm:</small>
          <div class="quick-suggests mt-1">
            ${data.suggested_questions.map(q => `
              <button class="suggest-btn" onclick="sendQuickPrompt('${q.replace(/'/g, "\\'")}')">
                ${q}
              </button>
            `).join("")}
          </div>
        </div>
      `;
    }

    botDiv.innerHTML = `
      <div class="message-bubble">
        <div class="chat-answer-body">${formattedReply}</div>
        ${suggestsHtml}
        <div class="mt-2 text-muted" style="font-size: 11px;">
          <i class="bi bi-shield-check text-success"></i> ${data.disclaimer}
        </div>
      </div>
    `;
    messagesBox.scrollTop = messagesBox.scrollHeight;

  } catch (err) {
    botDiv.innerHTML = `
      <div class="message-bubble text-danger">
        <p><i class="bi bi-exclamation-triangle-fill"></i> Không thể kết nối dịch vụ Chuyên gia AI: ${err.message}. Vui lòng thử lại sau.</p>
      </div>
    `;
  }
}

// Khi bấm vào câu hỏi đề xuất: Điền nội dung vào ô nhập liệu để người dùng kiểm tra hoặc chỉnh sửa, sau đó bấm Gửi mới bắt đầu hỏi
function sendQuickPrompt(promptText) {
  const input = document.getElementById("chatInputText");
  if (!input) return;
  input.value = promptText;
  input.focus();
  // Đưa con trỏ về cuối câu để người dùng có thể gõ thêm chi tiết
  input.setSelectionRange(input.value.length, input.value.length);
  input.classList.add("input-highlight");
  setTimeout(() => input.classList.remove("input-highlight"), 1200);
}

// 8. FORM NỘP YÊU CẦU BỒI THƯỜNG
async function openSubmitClaimModal() {
  const select = document.getElementById("submitPolicySelect");
  select.innerHTML = `<option value="">-- Đang nạp danh sách hợp đồng... --</option>`;
  try {
    const res = await fetch(`${API_BASE}/policies`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    const policies = await res.json();
    const activePolicies = policies.filter(p => p.status === "ACTIVE");

    select.innerHTML = "";
    if (activePolicies.length === 0) {
      select.innerHTML = `<option value="">Không có hợp đồng nào đang hiệu lực</option>`;
    } else {
      activePolicies.forEach(p => {
        const isAgentOrAdmin = currentUser && (currentUser.role === "agent" || currentUser.role === "admin");
        const label = isAgentOrAdmin
          ? `${p.policy_number} - KH: ${p.customer_name || 'Khách'} - ${p.product_name}`
          : `${p.policy_number} - ${p.product_name} (${formatVND(p.total_sum_insured)})`;
        select.innerHTML += `<option value="${p.id}">${label}</option>`;
      });
    }
  } catch (err) {
    console.error(err);
    select.innerHTML = `<option value="">Không thể tải danh sách hợp đồng</option>`;
  }

  document.getElementById("submitIncidentDate").value = new Date().toISOString().split("T")[0];
  document.getElementById("submitClaimModal").style.display = "flex";
}

function closeSubmitClaimModal() {
  document.getElementById("submitClaimModal").style.display = "none";
}

async function handleClaimSubmit() {
  const policySelect = document.getElementById("submitPolicySelect");
  const policyId = parseInt(policySelect.value);
  const incidentDateInput = document.getElementById("submitIncidentDate").value;
  const incidentDate = incidentDateInput ? `${incidentDateInput}T08:00:00` : new Date().toISOString();
  const claimAmount = parseNumberFromDots(document.getElementById("submitClaimAmount").value);
  const diagnosis = (document.getElementById("submitDiagnosis").value || "").trim();
  const hospital = (document.getElementById("submitHospitalName").value || "Bệnh viện đa khoa").trim();
  const docNotes = (document.getElementById("submitDocNotes").value || "").trim();

  if (!policyId) {
    showToast("Vui lòng chọn một hợp đồng bảo hiểm đang có hiệu lực!", "error");
    return;
  }
  if (isNaN(claimAmount) || claimAmount <= 0) {
    showToast("Vui lòng nhập số tiền viện phí thực tế hợp lệ (> 0 VNĐ)!", "error");
    document.getElementById("submitClaimAmount").focus();
    return;
  }
  if (!diagnosis) {
    showToast("Vui lòng nhập chẩn đoán bệnh viện hoặc lý do điều trị!", "error");
    document.getElementById("submitDiagnosis").focus();
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/claims`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({
        policy_id: policyId,
        incident_date: incidentDate,
        claimed_amount: claimAmount,
        diagnosis: diagnosis,
        hospital_name: hospital,
        documents: [
          {
            document_type: "Hóa đơn y tế & Bảng kê thanh toán",
            file_path: "uploads/claims/hoa_don_client.pdf",
            invoice_amount: claimAmount,
            notes: docNotes || "Hóa đơn điện tử viện phí đính kèm"
          }
        ]
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Nộp hồ sơ bồi thường thất bại.");
    }

    const newClaim = await res.json();
    showToast(`Nộp hồ sơ bồi thường thành công! Mã hồ sơ: ${newClaim.claim_number}`, "success");
    closeSubmitClaimModal();
    loadClaims();
    switchTab("claims");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// KHỞI TẠO: Mặc định điền thông tin tài khoản Giám định viên
window.addEventListener("DOMContentLoaded", () => {
  selectRolePreset("officer", false);

  window.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) {
      e.target.style.display = "none";
    }
  });

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-overlay").forEach(m => m.style.display = "none");
    }
  });
});
