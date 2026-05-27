const statusPill = document.getElementById("status-pill");
const modelPill = document.getElementById("model-pill");
const knowledgePill = document.getElementById("knowledge-pill");
const modePill = document.getElementById("mode-pill");
const chatStream = document.getElementById("chat-stream");
const modalOverlay = document.getElementById("modal-overlay");
const sideDrawer = document.getElementById("side-drawer");
const knowledgeModal = document.getElementById("knowledge-modal");
const bookingModal = document.getElementById("booking-modal");
const availabilityModal = document.getElementById("availability-modal");
const bookingAdminModal = document.getElementById("booking-admin-modal");
const escalationAdminModal = document.getElementById("escalation-admin-modal");
const memoryProfilesModal = document.getElementById("memory-profiles-modal");
const questionAnalyticsModal = document.getElementById("question-analytics-modal");
const adminLoginModal = document.getElementById("admin-login-modal");
const userRegisterModal = document.getElementById("user-register-modal");
const userLoginModal = document.getElementById("user-login-modal");
const adminLoginResponse = document.getElementById("admin-login-response");
const userRegisterResponse = document.getElementById("user-register-response");
const userLoginResponse = document.getElementById("user-login-response");
const bookingList = document.getElementById("booking-list");
const bookingAdminResponse = document.getElementById("booking-admin-response");
const bookingStatusFilter = document.getElementById("booking-status-filter");
const escalationList = document.getElementById("escalation-list");
const escalationAdminResponse = document.getElementById("escalation-admin-response");
const escalationStatusFilter = document.getElementById("escalation-status-filter");
const escalationRouteFilter = document.getElementById("escalation-route-filter");
const drawerModeTitle = document.getElementById("drawer-mode-title");
const userAuthPanel = document.getElementById("user-auth-panel");
const userSessionPanel = document.getElementById("user-session-panel");
const userSessionCopy = document.getElementById("user-session-copy");
const adminAuthPanel = document.getElementById("admin-auth-panel");
const adminSessionPanel = document.getElementById("admin-session-panel");
const adminSessionCopy = document.getElementById("admin-session-copy");
const serviceAdminDisclosure = document.querySelector(".service-admin-disclosure");
const serviceAdminResponse = document.getElementById("service-admin-response");
const serviceStatusList = document.getElementById("service-status-list");
const serviceAdminLastAction = document.getElementById("service-admin-last-action");
const serviceAdminLastTime = document.getElementById("service-admin-last-time");
const serviceAdminLastResult = document.getElementById("service-admin-last-result");
const refreshManagedServicesButton = document.getElementById("refresh-managed-services");
const startManagedServicesButton = document.getElementById("start-managed-services");
const restartManagedServicesButton = document.getElementById("restart-managed-services");
const stopManagedServicesButton = document.getElementById("stop-managed-services");
const openKnowledgeButton = document.getElementById("open-knowledge");
const openBookingListButton = document.getElementById("open-booking-list");
const openEscalationQueueButton = document.getElementById("open-escalation-queue");
const openMemoryProfilesButton = document.getElementById("open-memory-profiles");
const openQuestionAnalyticsButton = document.getElementById("open-question-analytics");
const openAvailabilityEditorButton = document.getElementById("open-availability-editor");
const assistantName = document.getElementById("assistant-name");
const topbarTitle = document.getElementById("topbar-title");
const topbarSubtitle = document.getElementById("topbar-subtitle");
const homepageLink = document.getElementById("homepage-link");
const chatQuestion = document.getElementById("chat-question");
const courseContextInput = document.getElementById("course-context");
const studentNameInput = document.getElementById("student-name");
const studentEmailInput = document.getElementById("student-email");
const profileDrawerCopy = document.getElementById("profile-drawer-copy");
const bookingStudentNameInput = document.getElementById("booking-student-name");
const bookingEmailInput = document.getElementById("booking-email");
const introQuickActions = document.querySelector(".intro-quick-actions");
const availabilityWeekLabel = document.getElementById("availability-week-label");
const availabilityResponse = document.getElementById("availability-response");
const availabilityGrid = document.getElementById("availability-grid");
const workflowShell = document.getElementById("workflow-shell");
const workflowTrace = document.getElementById("workflow-trace");
const workflowTraceWrap = document.getElementById("workflow-trace-wrap");
const workflowToggleButton = document.getElementById("workflow-toggle");
const workflowScrollLatestButton = document.getElementById("workflow-scroll-latest");
const workflowMobileHandle = document.getElementById("workflow-mobile-handle");
const workflowMobileHandleText = document.getElementById("workflow-mobile-handle-text");
const workflowMobileCloseButton = document.getElementById("workflow-mobile-close");
const workflowTotalDuration = document.getElementById("workflow-total-duration");
const workflowCurrentAction = document.getElementById("workflow-current-action");
const workflowKnowledgeCount = document.getElementById("workflow-knowledge-count");
const mobileWorkflowTrigger = document.getElementById("mobile-workflow-trigger");
const workflowMobileBackdrop = document.getElementById("workflow-mobile-backdrop");

const chatForm = document.getElementById("chat-form");
const adminLoginForm = document.getElementById("admin-login-form");
const userRegisterForm = document.getElementById("user-register-form");
const userLoginForm = document.getElementById("user-login-form");
const knowledgeForm = document.getElementById("knowledge-form");
const bookingForm = document.getElementById("booking-form");
const chatSubmitButton = chatForm.querySelector('button[type="submit"]');

const knowledgeResponse = document.getElementById("knowledge-response");
const bookingResponse = document.getElementById("booking-response");
const knowledgeList = document.getElementById("knowledge-list");
const memoryProfilesCategoryFilter = document.getElementById("memory-profiles-category");
const memoryProfilesStudentQuery = document.getElementById("memory-profiles-student-query");
const memoryProfilesResponse = document.getElementById("memory-profiles-response");
const memoryProfilesSummary = document.getElementById("memory-profiles-summary");
const memoryProfilesList = document.getElementById("memory-profiles-list");
const questionAnalyticsWindow = document.getElementById("question-analytics-window");
const questionAnalyticsResponse = document.getElementById("question-analytics-response");
const questionAnalyticsSummary = document.getElementById("question-analytics-summary");
const questionAnalyticsClusters = document.getElementById("question-analytics-clusters");
const questionAnalyticsGaps = document.getElementById("question-analytics-gaps");
const questionAnalyticsUnresolved = document.getElementById("question-analytics-unresolved");
const questionAnalyticsHandoffs = document.getElementById("question-analytics-handoffs");
const questionAnalyticsDrafts = document.getElementById("question-analytics-drafts");
const AVAILABILITY_SLOT_MINUTES = 30;
const AVAILABILITY_START_HOUR = 9;
const AVAILABILITY_END_HOUR = 18;
const AVAILABILITY_DAY_COUNT = 7;
const PROFILE_PROMPT_KEY = "myTwinProfilePromptShown";
const WORKFLOW_SHELL_COLLAPSED_KEY = "myTwinWorkflowShellCollapsed";
const WORKFLOW_MOBILE_MODE_KEY = "myTwinWorkflowMobileMode";
const LOCAL_API_PORT_CANDIDATES = ["55601", "8010", "8000"];
let assistantLabel = "我的学术分身";
let activeConversationId = createConversationId();
let activeWorkflowStream = null;
let activeWorkflowRequestId = null;
let activeWorkflowSteps = [];
let availabilityEditorState = null;
let workflowMobileHandlePointerId = null;
let workflowMobileHandleStartY = 0;
let suppressWorkflowMobileHandleClick = false;
let latestWorkflowMeta = {
    workflowAction: null,
    knowledgeHits: null,
    isStreaming: false,
};
let latestManagedServiceEvent = null;
let isAdminSession = false;
let isUserAuthenticated = false;
let resolvedApiOrigin = typeof globalThis.__SAGE_FACULTY_TWIN_API_ORIGIN__ === "string"
    ? globalThis.__SAGE_FACULTY_TWIN_API_ORIGIN__.trim()
    : "";
let apiOriginResolutionPromise = null;
const adminOnlyDrawerButtons = [
    openKnowledgeButton,
    openAvailabilityEditorButton,
    openBookingListButton,
    openEscalationQueueButton,
    openMemoryProfilesButton,
    openQuestionAnalyticsButton,
].filter(Boolean);
const adminOnlyModals = [
    knowledgeModal,
    availabilityModal,
    bookingAdminModal,
    escalationAdminModal,
    memoryProfilesModal,
    questionAnalyticsModal,
].filter(Boolean);
const managedServiceButtons = [
    {
        action: "status",
        element: refreshManagedServicesButton,
        idleLabel: "刷新服务状态",
        busyLabel: "正在刷新...",
    },
    {
        action: "start",
        element: startManagedServicesButton,
        idleLabel: "启动服务",
        busyLabel: "正在启动...",
    },
    {
        action: "restart",
        element: restartManagedServicesButton,
        idleLabel: "重启服务",
        busyLabel: "正在重启...",
    },
    {
        action: "stop",
        element: stopManagedServicesButton,
        idleLabel: "关闭服务",
        busyLabel: "正在关闭...",
    },
].filter(({ element }) => Boolean(element));
const submittedFeedbackExchangeIds = new Set();

if (workflowTrace) {
    workflowTrace.addEventListener("click", handleWorkflowTraceToggle);
}

chatStream?.addEventListener("click", handleMessageSectionToggle);

workflowToggleButton?.addEventListener("click", toggleWorkflowShell);
workflowScrollLatestButton?.addEventListener("click", scrollWorkflowToLatest);
workflowMobileHandle?.addEventListener("click", toggleWorkflowMobileSheetMode);
workflowMobileHandle?.addEventListener("pointerdown", handleWorkflowMobileHandlePointerDown);
workflowMobileHandle?.addEventListener("pointermove", handleWorkflowMobileHandlePointerMove);
workflowMobileHandle?.addEventListener("pointerup", handleWorkflowMobileHandlePointerUp);
workflowMobileHandle?.addEventListener("pointercancel", resetWorkflowMobileHandlePointer);
workflowMobileCloseButton?.addEventListener("click", closeWorkflowMobileSheet);
mobileWorkflowTrigger?.addEventListener("click", toggleWorkflowMobileSheet);
workflowMobileBackdrop?.addEventListener("click", closeWorkflowMobileSheet);
globalThis.addEventListener("resize", syncWorkflowViewportState);
introQuickActions?.addEventListener("click", handleIntroQuickActionClick);

document.getElementById("open-drawer").addEventListener("click", openDrawer);
document.querySelectorAll("[data-close-drawer]").forEach((button) => {
    button.addEventListener("click", closeDrawer);
});
document.getElementById("open-user-register")?.addEventListener("click", () => {
    closeDrawer();
    openModal(userRegisterModal);
});
document.getElementById("open-user-login")?.addEventListener("click", () => {
    closeDrawer();
    openModal(userLoginModal);
});
document.getElementById("open-knowledge").addEventListener("click", async () => {
    if (!ensureAdminOnlyAccess({ openLogin: true })) {
        return;
    }
    closeDrawer();
    openModal(knowledgeModal);
    await loadKnowledgeList();
});
document.getElementById("open-booking").addEventListener("click", () => {
    bookingStudentNameInput.value = studentNameInput.value;
    bookingEmailInput.value = studentEmailInput.value;
    openModal(bookingModal);
});
document.getElementById("open-booking-list").addEventListener("click", async () => {
    if (!ensureAdminOnlyAccess({ openLogin: true })) {
        return;
    }
    closeDrawer();
    openModal(bookingAdminModal);
    await loadBookingList();
});
document.getElementById("open-escalation-queue").addEventListener("click", async () => {
    if (!ensureAdminOnlyAccess({ openLogin: true })) {
        return;
    }
    closeDrawer();
    openModal(escalationAdminModal);
    await loadEscalationList();
});
document.getElementById("open-memory-profiles").addEventListener("click", async () => {
    if (!ensureAdminOnlyAccess({ openLogin: true })) {
        return;
    }
    closeDrawer();
    openModal(memoryProfilesModal);
    await loadMemoryProfiles();
});
document.getElementById("open-question-analytics").addEventListener("click", async () => {
    if (!ensureAdminOnlyAccess({ openLogin: true })) {
        return;
    }
    closeDrawer();
    openModal(questionAnalyticsModal);
    await loadQuestionAnalytics();
});
document.getElementById("open-availability-editor").addEventListener("click", async () => {
    if (!ensureAdminOnlyAccess({ openLogin: true })) {
        return;
    }
    closeDrawer();
    openModal(availabilityModal);
    await loadAvailabilityEditor();
});
document.getElementById("open-admin-login").addEventListener("click", () => {
    closeDrawer();
    openModal(adminLoginModal);
});
document.getElementById("admin-logout").addEventListener("click", handleAdminLogout);
document.getElementById("user-logout")?.addEventListener("click", handleUserLogout);
document.getElementById("refresh-managed-services")?.addEventListener("click", async () => {
    await loadManagedServices();
});
document.getElementById("start-managed-services")?.addEventListener("click", async () => {
    await controlManagedServices("start");
});
document.getElementById("restart-managed-services")?.addEventListener("click", async () => {
    await controlManagedServices("restart");
});
document.getElementById("stop-managed-services")?.addEventListener("click", async () => {
    await controlManagedServices("stop");
});
document.getElementById("refresh-booking-list").addEventListener("click", async () => {
    await loadBookingList();
});
document.getElementById("refresh-escalation-list").addEventListener("click", async () => {
    await loadEscalationList();
});
document.getElementById("refresh-memory-profiles").addEventListener("click", async () => {
    await loadMemoryProfiles();
});
document.getElementById("refresh-question-analytics").addEventListener("click", async () => {
    await loadQuestionAnalytics();
});
memoryProfilesCategoryFilter?.addEventListener("change", async () => {
    await loadMemoryProfiles();
});
questionAnalyticsWindow?.addEventListener("change", async () => {
    await loadQuestionAnalytics();
});
memoryProfilesStudentQuery?.addEventListener("keydown", async (event) => {
    if (event.key !== "Enter") {
        return;
    }
    event.preventDefault();
    await loadMemoryProfiles();
});
document.getElementById("save-availability").addEventListener("click", saveAvailabilityEditor);
document.getElementById("apply-workday-morning-template").addEventListener("click", () => {
    applyAvailabilityTemplate("workday-morning");
});
document.getElementById("apply-workday-full-template").addEventListener("click", () => {
    applyAvailabilityTemplate("workday-full");
});
document.getElementById("apply-workday-afternoon-template").addEventListener("click", () => {
    applyAvailabilityTemplate("workday-afternoon");
});
document.getElementById("copy-previous-week-template").addEventListener("click", copyPreviousWeekTemplate);
document.getElementById("clear-availability").addEventListener("click", clearAvailabilityEditor);
bookingStatusFilter?.addEventListener("change", async () => {
    await loadBookingList();
});
escalationStatusFilter?.addEventListener("change", async () => {
    await loadEscalationList();
});
escalationRouteFilter?.addEventListener("change", async () => {
    await loadEscalationList();
});
questionAnalyticsGaps?.addEventListener("click", handleKnowledgeGapDraftAction);
questionAnalyticsDrafts?.addEventListener("click", handleKnowledgeGapDraftAction);
modalOverlay.addEventListener("click", closeModals);
document.querySelectorAll("[data-close-modal]").forEach((button) => {
    button.addEventListener("click", closeModals);
});
bookingList.addEventListener("click", handleBookingApprovalClick);
escalationList?.addEventListener("click", handleEscalationResolveClick);
availabilityGrid.addEventListener("click", handleAvailabilityGridClick);

document.getElementById("load-demo-chat").addEventListener("click", () => {
    seedChatQuestion("和老师约时间前，我应该先准备什么？", "科研指导");
    closeDrawer();
});

document.getElementById("refresh-knowledge").addEventListener("click", async () => {
    await loadKnowledgeList();
});

adminLoginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setInlineStatus(adminLoginResponse, "正在核对管理员身份...", "empty");
    try {
        const data = await apiRequest("/auth/admin/login", {
            method: "POST",
            body: JSON.stringify({
                username: document.getElementById("admin-username").value,
                password: document.getElementById("admin-password").value,
            }),
        });
        setInlineStatus(adminLoginResponse, `已使用 ${data.username} 登录。`, "success");
        document.getElementById("admin-password").value = "";
        await refreshSession();
        closeModals();
    } catch (error) {
        setInlineStatus(adminLoginResponse, error.message, "error");
    }
});

userRegisterForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    setInlineStatus(userRegisterResponse, "正在创建账号...", "empty");
    try {
        await apiRequest("/auth/user/register", {
            method: "POST",
            body: JSON.stringify({
                name: document.getElementById("user-register-name").value,
                email: document.getElementById("user-register-email").value,
                password: document.getElementById("user-register-password").value,
            }),
        });
        document.getElementById("user-register-password").value = "";
        setInlineStatus(userRegisterResponse, "账号已创建，当前已自动登录。", "success");
        await refreshUserSession();
        closeModals();
    } catch (error) {
        setInlineStatus(userRegisterResponse, error.message, "error");
    }
});

userLoginForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    setInlineStatus(userLoginResponse, "正在登录账号...", "empty");
    try {
        await apiRequest("/auth/user/login", {
            method: "POST",
            body: JSON.stringify({
                email: document.getElementById("user-login-email").value,
                password: document.getElementById("user-login-password").value,
            }),
        });
        document.getElementById("user-login-password").value = "";
        setInlineStatus(userLoginResponse, "已登录当前账号。", "success");
        await refreshUserSession();
        closeModals();
    } catch (error) {
        setInlineStatus(userLoginResponse, error.message, "error");
    }
});

chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = document.getElementById("chat-question").value.trim();
    if (!question) {
        return;
    }

    const payload = {
        student_name: document.getElementById("student-name").value,
        student_email: document.getElementById("student-email").value || null,
        course_context: document.getElementById("course-context").value || null,
        question,
        conversation_id: activeConversationId,
    };
    const workflowRequestId = createConversationId();

    appendMessage("user", payload.student_name || "学生", question, { emphasis: "user" });
    const pendingMessage = appendMessage("assistant", assistantLabel, "正在整理问题、检索资料并准备回复", {
        state: "pending",
    });
    document.getElementById("chat-question").value = "";
    autoResizeTextarea();
    chatSubmitButton.disabled = true;
    chatSubmitButton.textContent = "发送中";
    await openWorkflowTraceStream(workflowRequestId);
    if (isMobileWorkflowViewport()) {
        openWorkflowMobileSheet("full");
    }

    try {
        const data = await apiRequest(`/chat?request_id=${encodeURIComponent(workflowRequestId)}`, {
            method: "POST",
            body: JSON.stringify(payload),
            timeoutMs: 45000,
        });
        activeConversationId = data.conversation_id || activeConversationId;
        stopWorkflowTraceStream();
        renderWorkflowTrace(data.workflow_trace || [], {
            workflowAction: data.workflow_action || null,
            knowledgeHits: Array.isArray(data.knowledge_hits) ? data.knowledge_hits.length : null,
            isStreaming: false,
        });
        renderAssistantMessage(
            pendingMessage,
            data.answer,
            data.answer_basis || [],
            data.follow_up_actions || [],
            data.knowledge_hits || [],
            data.booking_result || null,
            false,
            data.exchange_id || null
        );
    } catch (error) {
        stopWorkflowTraceStream();
        renderWorkflowTraceError(error.message);
        renderAssistantMessage(pendingMessage, error.message, [], [], [], null, true, null);
    } finally {
        chatSubmitButton.disabled = false;
        chatSubmitButton.textContent = "发送";
    }
});

knowledgeForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!ensureAdminOnlyAccess({ responseElement: knowledgeResponse })) {
        return;
    }
    setInlineStatus(knowledgeResponse, "正在保存资料...", "empty");
    const payload = {
        title: document.getElementById("knowledge-title").value,
        source_name: document.getElementById("knowledge-source").value || null,
        content: document.getElementById("knowledge-content").value,
        tags: document
            .getElementById("knowledge-tags")
            .value.split(",")
            .map((item) => item.trim())
            .filter(Boolean),
    };

    try {
        const data = await apiRequest("/knowledge", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        setInlineStatus(knowledgeResponse, `已保存：${data.title}`, "success");
        await refreshStatus();
        await loadKnowledgeList();
    } catch (error) {
        setInlineStatus(knowledgeResponse, error.message, "error");
    }
});

bookingForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setInlineStatus(bookingResponse, "正在提交预约，请确认主题和时间无误...", "empty");
    const payload = {
        student_name: document.getElementById("booking-student-name").value,
        student_email: document.getElementById("booking-email").value,
        topic: document.getElementById("booking-topic").value,
        preferred_start: toIso(document.getElementById("booking-start").value),
        preferred_end: toIso(document.getElementById("booking-end").value),
    };

    try {
        const data = await apiRequest("/bookings", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        renderBookingResponseStatus(bookingResponse, data, {
            state: data.accepted ? "success" : "error",
            lines: data.accepted
                ? [
                    `预约编号：${data.booking.booking_id}`,
                    `当前状态：${data.booking.status}`,
                ]
                : [`可选时间：${(data.alternative_slots || []).join(", ") || "无"}`],
        });
    } catch (error) {
        setInlineStatus(bookingResponse, error.message, "error");
    }
});

document.getElementById("chat-question").addEventListener("input", autoResizeTextarea);

function handleIntroQuickActionClick(event) {
    const trigger = event.target.closest("[data-seed-question]");
    if (!(trigger instanceof HTMLElement)) {
        return;
    }
    const question = trigger.dataset.seedQuestion?.trim();
    if (!question) {
        return;
    }
    seedChatQuestion(question, trigger.dataset.seedContext || "");
}

function seedChatQuestion(question, courseContext = "") {
    chatQuestion.value = question;
    if (courseContextInput && courseContext) {
        courseContextInput.value = courseContext;
    }
    autoResizeTextarea();
    chatQuestion.focus();
}

async function refreshStatus() {
    try {
        const data = await apiRequest("/health", { timeoutMs: 5000 });
        applyBranding(data.owner_name, data.owner_role, data.homepage_public_url);
        statusPill.textContent = data.status === "ok" ? "服务正常" : `状态 ${data.status}`;
        modelPill.textContent = "连接已就绪";
        knowledgePill.textContent = `知识库 ${data.knowledge_documents}`;
    } catch (error) {
        applyBranding(null, null, "");
        statusPill.textContent = "服务不可用";
        modelPill.textContent = "连接状态未知";
        knowledgePill.textContent = "知识库未知";
    }
}

async function refreshSession() {
    try {
        const data = await apiRequest("/auth/session", { timeoutMs: 5000 });
        const isAdmin = Boolean(data.is_admin);
        isAdminSession = isAdmin;
        modePill.textContent = isAdmin ? `管理员模式${data.username ? ` · ${data.username}` : ""}` : "普通用户模式";
        drawerModeTitle.textContent = isAdmin ? "管理员模式" : "普通用户模式";
        adminAuthPanel.classList.toggle("hidden", isAdmin);
        adminSessionPanel.classList.toggle("hidden", !isAdmin);
        openKnowledgeButton.classList.toggle("hidden", !isAdmin);
        openBookingListButton.classList.toggle("hidden", !isAdmin);
        openEscalationQueueButton.classList.toggle("hidden", !isAdmin);
        openMemoryProfilesButton.classList.toggle("hidden", !isAdmin);
        openQuestionAnalyticsButton.classList.toggle("hidden", !isAdmin);
        openAvailabilityEditorButton.classList.toggle("hidden", !isAdmin);
        adminSessionCopy.textContent = isAdmin
            ? `当前管理员：${data.username || "admin"}`
            : "当前未登录管理员。";
        setAdminOnlyAccess(isAdmin);
        setManagedServiceAccess(isAdmin);
        if (isAdmin) {
            await loadManagedServices();
        } else {
            resetManagedServicePanel();
        }
    } catch (error) {
        isAdminSession = false;
        modePill.textContent = "普通用户模式";
        drawerModeTitle.textContent = "普通用户模式";
        adminAuthPanel.classList.remove("hidden");
        adminSessionPanel.classList.add("hidden");
        openKnowledgeButton.classList.add("hidden");
        openBookingListButton.classList.add("hidden");
        openEscalationQueueButton.classList.add("hidden");
        openMemoryProfilesButton.classList.add("hidden");
        openQuestionAnalyticsButton.classList.add("hidden");
        openAvailabilityEditorButton.classList.add("hidden");
        adminSessionCopy.textContent = "当前未登录管理员。";
        setAdminOnlyAccess(false);
        setManagedServiceAccess(false);
        resetManagedServicePanel();
    }
}

async function refreshUserSession() {
    try {
        const data = await apiRequest("/auth/user/session", { timeoutMs: 5000 });
        applyUserSession(data);
    } catch (error) {
        applyUserSession({ is_authenticated: false, mode: "guest", account: null });
    }
}

function applyUserSession(session) {
    const wasAuthenticated = isUserAuthenticated;
    const authenticated = Boolean(session?.is_authenticated && session?.account);
    isUserAuthenticated = authenticated;

    userAuthPanel?.classList.toggle("hidden", authenticated);
    userSessionPanel?.classList.toggle("hidden", !authenticated);

    if (authenticated) {
        const account = session.account;
        userSessionCopy.textContent = `当前账号：${account.name} · ${account.email}`;
        studentNameInput.value = account.name;
        studentEmailInput.value = account.email;
        bookingStudentNameInput.value = account.name;
        bookingEmailInput.value = account.email;
        studentNameInput.readOnly = true;
        studentEmailInput.readOnly = true;
        profileDrawerCopy.textContent = "当前已绑定登录账号。聊天记录和预约申请会默认使用该账号的姓名与邮箱。";
        return;
    }

    userSessionCopy.textContent = "当前未登录用户账号。";
    studentNameInput.readOnly = false;
    studentEmailInput.readOnly = false;
    profileDrawerCopy.textContent = "先把姓名和邮箱填对。后面的问答记录、预约确认和跟进都会直接用这两个字段。";

    if (wasAuthenticated) {
        studentNameInput.value = "guest";
        studentEmailInput.value = "";
        bookingStudentNameInput.value = "guest";
        bookingEmailInput.value = "";
    }
}

async function loadManagedServices() {
    if (!ensureManagedServiceAccess()) {
        return;
    }
    if (!serviceAdminResponse || !serviceStatusList) {
        return;
    }
    setManagedServiceControlsBusy("status", true);
    beginManagedServiceAction("status", "正在读取当前服务状态，请稍候。", { success: true });
    setInlineStatus(serviceAdminResponse, "正在读取当前服务状态...", "empty");
    try {
        const data = await apiRequest("/admin/services", { timeoutMs: 10000 });
        renderManagedServices(data.services || []);
        updateManagedServiceSummary({
            action: "status",
            success: Boolean(data.success),
            message: data.message || "服务状态已更新。",
        });
        setInlineStatus(serviceAdminResponse, data.message || "服务状态已更新。", data.success ? "success" : "error");
    } catch (error) {
        serviceStatusList.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(error.message)}</p></div>`;
        updateManagedServiceSummary({
            action: "status",
            success: false,
            message: error.message,
        });
        setInlineStatus(serviceAdminResponse, error.message, "error");
    } finally {
        setManagedServiceControlsBusy("status", false);
    }
}

async function controlManagedServices(action) {
    if (!ensureManagedServiceAccess()) {
        return;
    }
    if (!serviceAdminResponse) {
        return;
    }
    const actionLabel = action === "start" ? "启动" : action === "stop" ? "关闭" : "重启";
    const pendingMessage = buildManagedServicePendingMessage(action);
    setManagedServiceControlsBusy(action, true);
    beginManagedServiceAction(action, pendingMessage, { success: true });
    setInlineStatus(serviceAdminResponse, pendingMessage, "empty");
    try {
        const data = await apiRequest(`/admin/services/${encodeURIComponent(action)}`, {
            method: "POST",
            timeoutMs: 30000,
        });
        renderManagedServices(data.services || []);
        const successMessage = buildManagedServiceSuccessMessage(action, data.message);
        updateManagedServiceSummary({
            action,
            success: Boolean(data.success),
            message: Boolean(data.success) ? successMessage : data.message || `服务${actionLabel}失败。`,
        });
        setInlineStatus(
            serviceAdminResponse,
            Boolean(data.success) ? successMessage : data.message || `服务${actionLabel}失败。`,
            data.success ? "success" : "error"
        );
    } catch (error) {
        updateManagedServiceSummary({
            action,
            success: false,
            message: error.message,
        });
        setInlineStatus(serviceAdminResponse, error.message, "error");
    } finally {
        setManagedServiceControlsBusy(action, false);
    }
}

function setManagedServiceControlsBusy(activeAction, isBusy) {
    managedServiceButtons.forEach(({ action, element, idleLabel, busyLabel }) => {
        if (!element) {
            return;
        }
        const isActive = isBusy && action === activeAction;
        element.disabled = isBusy;
        element.textContent = isActive ? busyLabel : idleLabel;
        if (isActive) {
            element.setAttribute("aria-busy", "true");
        } else {
            element.removeAttribute("aria-busy");
        }
    });
}

function setAdminOnlyAccess(enabled) {
    adminOnlyDrawerButtons.forEach((button) => {
        button.classList.toggle("hidden", !enabled);
        button.disabled = !enabled;
        button.setAttribute("aria-disabled", String(!enabled));
    });
    if (!enabled) {
        closeAdminOnlyModals();
    }
}

function closeAdminOnlyModals() {
    adminOnlyModals.forEach((modal) => {
        modal.classList.add("hidden");
        modal.setAttribute("aria-hidden", "true");
    });
    if (
        sideDrawer.classList.contains("hidden") &&
        knowledgeModal.classList.contains("hidden") &&
        bookingModal.classList.contains("hidden") &&
        adminLoginModal.classList.contains("hidden") &&
        availabilityModal.classList.contains("hidden") &&
        bookingAdminModal.classList.contains("hidden") &&
        escalationAdminModal.classList.contains("hidden") &&
        memoryProfilesModal.classList.contains("hidden") &&
        questionAnalyticsModal.classList.contains("hidden")
    ) {
        modalOverlay.classList.add("hidden");
    }
    syncFloatingWorkflowTriggerState();
}

function ensureAdminOnlyAccess(options = {}) {
    if (isAdminSession) {
        return true;
    }
    if (options.responseElement) {
        setInlineStatus(options.responseElement, "请先登录管理员模式，再访问这个管理入口。", "error");
    }
    if (options.openLogin) {
        closeDrawer();
        openModal(adminLoginModal);
        setInlineStatus(adminLoginResponse, "请先登录管理员模式，再访问这个管理入口。", "error");
    }
    return false;
}

function setManagedServiceAccess(enabled) {
    if (serviceAdminDisclosure) {
        serviceAdminDisclosure.hidden = !enabled;
        if (!enabled) {
            serviceAdminDisclosure.open = false;
        }
    }
    managedServiceButtons.forEach(({ element, idleLabel }) => {
        if (!element) {
            return;
        }
        element.disabled = !enabled;
        element.textContent = idleLabel;
        element.setAttribute("aria-disabled", String(!enabled));
        element.removeAttribute("aria-busy");
    });
}

function ensureManagedServiceAccess() {
    if (isAdminSession) {
        return true;
    }
    if (serviceAdminResponse) {
        setInlineStatus(serviceAdminResponse, "请先登录管理员模式，再执行服务维护操作。", "error");
    }
    return false;
}

function beginManagedServiceAction(action, message, options = {}) {
    latestManagedServiceEvent = {
        action,
        success: Boolean(options.success),
        message,
        timestamp: new Date(),
        inProgress: true,
    };
    renderManagedServiceSummary();
}

function updateManagedServiceSummary(event) {
    latestManagedServiceEvent = {
        action: event.action,
        success: Boolean(event.success),
        message: event.message || "",
        timestamp: new Date(),
        inProgress: false,
    };
    renderManagedServiceSummary();
}

function renderManagedServiceSummary() {
    if (!serviceAdminLastAction || !serviceAdminLastTime || !serviceAdminLastResult) {
        return;
    }

    if (!latestManagedServiceEvent) {
        serviceAdminLastAction.textContent = "尚未执行";
        serviceAdminLastTime.textContent = "--";
        serviceAdminLastResult.textContent = "需要维护时再操作，平时不用动服务。";
        return;
    }

    serviceAdminLastAction.textContent = formatManagedServiceActionLabel(latestManagedServiceEvent.action);
    serviceAdminLastTime.textContent = latestManagedServiceEvent.inProgress
        ? "执行中"
        : formatManagedServiceTimestamp(latestManagedServiceEvent.timestamp);
    serviceAdminLastResult.textContent = latestManagedServiceEvent.message || (latestManagedServiceEvent.success ? "操作成功。" : "操作失败。");
}

function formatManagedServiceActionLabel(action) {
    switch (action) {
        case "status":
            return "刷新状态";
        case "start":
            return "启动服务";
        case "stop":
            return "关闭服务";
        case "restart":
            return "重启服务";
        default:
            return action || "未知操作";
    }
}

function formatManagedServiceTimestamp(timestamp) {
    const value = timestamp instanceof Date ? timestamp : new Date(timestamp);
    if (Number.isNaN(value.getTime())) {
        return "--";
    }
    return value.toLocaleString("zh-CN", {
        hour12: false,
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
}

function buildManagedServicePendingMessage(action) {
    switch (action) {
        case "start":
            return "正在启动服务，请等待状态恢复。";
        case "stop":
            return "正在关闭服务，请等待状态刷新。";
        case "restart":
            return "正在重启服务，应用和代理会短暂中断，请等待状态恢复。";
        default:
            return "正在读取当前服务状态，请稍候。";
    }
}

function buildManagedServiceSuccessMessage(action, fallbackMessage) {
    switch (action) {
        case "start":
            return "启动指令已提交，服务状态已刷新。";
        case "stop":
            return "关闭指令已提交，服务状态已刷新。";
        case "restart":
            return "重启指令已提交，服务状态已刷新。";
        default:
            return fallbackMessage || "服务状态已更新。";
    }
}

function renderManagedServices(services) {
    if (!serviceStatusList) {
        return;
    }
    serviceStatusList.innerHTML = "";
    if (!Array.isArray(services) || !services.length) {
        serviceStatusList.innerHTML = '<div class="list-card"><p class="list-body">暂无服务状态。</p></div>';
        return;
    }

    services.forEach((item) => {
        const card = document.createElement("article");
        card.className = "list-card list-card-service";
        const activeLabel = item.active_state === "active" ? "运行中" : item.active_state === "inactive" ? "已停止" : item.active_state;
        card.innerHTML = `
            <h3>${escapeHtml(item.name)}</h3>
            <p class="list-meta">${escapeHtml(item.description || item.unit)}</p>
            <div class="list-card-actions">
                <span class="status-badge ${escapeHtml(item.active_state === "active" ? "status-badge-confirmed" : "status-badge-pending")}">${escapeHtml(activeLabel)}</span>
                <span class="list-meta">${escapeHtml(item.unit)} · ${escapeHtml(item.sub_state)}</span>
            </div>
        `;
        serviceStatusList.appendChild(card);
    });
}

function resetManagedServicePanel() {
    latestManagedServiceEvent = null;
    setManagedServiceControlsBusy("status", false);
    if (serviceStatusList) {
        serviceStatusList.innerHTML = "";
    }
    if (serviceAdminResponse) {
        setInlineStatus(serviceAdminResponse, "需要维护时再操作，平时不用动服务。", "empty");
    }
    renderManagedServiceSummary();
}

async function loadKnowledgeList() {
    if (!ensureAdminOnlyAccess({ responseElement: knowledgeResponse })) {
        return;
    }
    try {
        const documents = await apiRequest("/knowledge");
        knowledgeList.innerHTML = "";
        if (!documents.length) {
            knowledgeList.innerHTML = '<div class="list-card"><p class="list-body">暂无资料。</p></div>';
            return;
        }

        documents
            .slice()
            .reverse()
            .forEach((record) => {
                const card = document.createElement("article");
                card.className = "list-card list-card-knowledge";
                const tags = (record.tags || []).join(", ") || "无";
                card.innerHTML = `
                    <h3>${escapeHtml(record.title)}</h3>
                    <p class="list-meta">${escapeHtml(record.source_name || "手动录入")} | 标签：${escapeHtml(tags)}</p>
                    <p class="list-body">${escapeHtml(record.content)}</p>
        `;
                knowledgeList.appendChild(card);
            });
    } catch (error) {
        knowledgeList.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(error.message)}</p></div>`;
    }
}

async function loadBookingList() {
    if (!ensureAdminOnlyAccess({ responseElement: bookingAdminResponse })) {
        return;
    }
    const selectedStatus = bookingStatusFilter?.value ?? "待确认";
    const statusLabel = selectedStatus || "全部状态";
    setInlineStatus(bookingAdminResponse, `正在加载${statusLabel}预约...`, "empty");
    bookingList.innerHTML = `<div class="list-card"><p class="list-body">正在加载${escapeHtml(statusLabel)}预约...</p></div>`;
    try {
        const query = selectedStatus ? `?status=${encodeURIComponent(selectedStatus)}` : "";
        const bookings = await apiRequest(`/bookings${query}`);
        bookingList.innerHTML = "";
        if (!bookings.length) {
            bookingList.innerHTML = `<div class="list-card"><p class="list-body">当前没有${escapeHtml(statusLabel)}预约。</p></div>`;
            setInlineStatus(bookingAdminResponse, `当前没有${statusLabel}预约。`, "success");
            return;
        }

        bookings
            .slice()
            .reverse()
            .forEach((booking) => {
                const card = document.createElement("article");
                card.className = `list-card list-card-booking ${booking.status === "待确认" ? "list-card-booking-pending" : "list-card-booking-resolved"}`;
                const isPending = booking.status === "待确认";
                const reasonHtml = booking.rejection_reason
                    ? `<p class="list-body booking-reason-copy">拒绝原因：${escapeHtml(booking.rejection_reason)}</p>`
                    : "";
                const actionsHtml = isPending
                    ? `
                        <div class="booking-reason-field">
                            <label>
                                <span>拒绝原因</span>
                                <textarea rows="2" placeholder="例如：这周日程已满，请改约下周。" data-booking-rejection-reason="${escapeHtml(booking.booking_id)}"></textarea>
                            </label>
                        </div>
                        <div class="inline-action-group">
                            <button type="button" class="primary-button inline-action-button" data-booking-confirm="${escapeHtml(booking.booking_id)}">确认预约</button>
                            <button type="button" class="ghost-button inline-action-button" data-booking-reject="${escapeHtml(booking.booking_id)}">拒绝预约</button>
                        </div>
                    `
                    : "";
                card.innerHTML = `
          <h3>${escapeHtml(booking.topic)}</h3>
          <p class="list-meta">${escapeHtml(booking.student_name)} | ${escapeHtml(booking.student_email)}</p>
          <p class="list-body">${escapeHtml(formatBookingWindow(booking.start_at, booking.end_at))}</p>
          ${reasonHtml}
          <div class="list-card-actions">
            <span class="status-badge ${escapeHtml(statusBadgeClassName(booking.status))}">${escapeHtml(booking.status)}</span>
            ${actionsHtml}
          </div>
        `;
                bookingList.appendChild(card);
            });
        setInlineStatus(bookingAdminResponse, `共有 ${bookings.length} 条${statusLabel}预约。`, "empty");
    } catch (error) {
        bookingList.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(error.message)}</p></div>`;
        setInlineStatus(bookingAdminResponse, error.message, "error");
    }
}

async function loadMemoryProfiles() {
    if (!ensureAdminOnlyAccess({ responseElement: memoryProfilesResponse })) {
        return;
    }
    setInlineStatus(memoryProfilesResponse, "正在加载学生长期记录...", "empty");
    memoryProfilesSummary.innerHTML = "";
    memoryProfilesList.innerHTML = '<div class="list-card"><p class="list-body">正在加载学生长期记录...</p></div>';

    const category = memoryProfilesCategoryFilter?.value?.trim() || "";
    const studentQuery = memoryProfilesStudentQuery?.value?.trim() || "";
    const params = new URLSearchParams({ limit: "50" });
    if (category) {
        params.set("category", category);
    }
    if (studentQuery) {
        params.set("student_query", studentQuery);
    }

    try {
        const data = await apiRequest(`/memory/profiles?${params.toString()}`);
        const profiles = Array.isArray(data.profiles) ? data.profiles : [];
        syncMemoryProfileCategoryOptions(data.available_categories || []);
        renderMemoryProfileSummary(data.category_counts || {});
        memoryProfilesList.innerHTML = "";

        if (!profiles.length) {
            memoryProfilesList.innerHTML = '<div class="list-card"><p class="list-body">当前没有符合条件的学生记录。</p></div>';
            setInlineStatus(memoryProfilesResponse, "当前没有符合条件的学生记录。", "success");
            return;
        }

        profiles.forEach((profile) => {
            const card = document.createElement("article");
            card.className = "list-card list-card-memory";
            const studentLabel = [profile.student_name || profile.student_key, profile.student_email || "未提供邮箱"]
                .filter(Boolean)
                .join(" | ");
            card.innerHTML = `
                <h3>${escapeHtml(profile.summary)}</h3>
                <p class="list-meta">${escapeHtml(studentLabel)} | ${escapeHtml(profile.student_key)}</p>
                <p class="list-body">${escapeHtml(profile.evidence || "暂无")}</p>
                <div class="list-card-actions">
                    <span class="status-badge">${escapeHtml(formatProfileCategoryLabel(profile.category))}</span>
                    <span class="list-meta">更新于 ${escapeHtml(formatDateTime(profile.updated_at))}</span>
                </div>
            `;
            memoryProfilesList.appendChild(card);
        });

        setInlineStatus(
            memoryProfilesResponse,
            `共加载 ${profiles.length} 条学生长期记录。`,
            "empty"
        );
    } catch (error) {
        memoryProfilesSummary.innerHTML = "";
        memoryProfilesList.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(error.message)}</p></div>`;
        setInlineStatus(memoryProfilesResponse, error.message, "error");
    }
}

async function loadQuestionAnalytics() {
    if (!ensureAdminOnlyAccess({ responseElement: questionAnalyticsResponse })) {
        return;
    }
    if (!questionAnalyticsResponse) {
        return;
    }

    const days = questionAnalyticsWindow?.value || "7";
    setInlineStatus(questionAnalyticsResponse, `正在生成最近 ${days} 天问答周报...`, "empty");
    questionAnalyticsSummary.innerHTML = "";
    questionAnalyticsClusters.innerHTML = '<div class="list-card"><p class="list-body">正在分析高频问题...</p></div>';
    questionAnalyticsGaps.innerHTML = '<div class="list-card"><p class="list-body">正在生成知识缺口建议...</p></div>';
    questionAnalyticsUnresolved.innerHTML = '<div class="list-card"><p class="list-body">正在汇总未解决问题...</p></div>';
    questionAnalyticsHandoffs.innerHTML = '<div class="list-card"><p class="list-body">正在统计人工接管热点...</p></div>';
    questionAnalyticsDrafts.innerHTML = '<div class="list-card"><p class="list-body">正在加载待补知识草稿...</p></div>';

    try {
        const report = await apiRequest(`/analytics/questions?days=${encodeURIComponent(days)}`);
        const drafts = await apiRequest("/analytics/questions/gap-drafts");
        renderQuestionAnalyticsSummary(report.overview || {});
        renderQuestionAnalyticsClusters(report.top_clusters || []);
        renderQuestionAnalyticsGaps(report.knowledge_gap_suggestions || []);
        renderQuestionAnalyticsUnresolved(report.unresolved_questions || []);
        renderQuestionAnalyticsHandoffs(report.handoff_categories || []);
        renderQuestionAnalyticsDrafts(drafts || []);
        setInlineStatus(questionAnalyticsResponse, `已生成最近 ${days} 天问答周报。`, "success");
    } catch (error) {
        questionAnalyticsSummary.innerHTML = "";
        questionAnalyticsClusters.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(error.message)}</p></div>`;
        questionAnalyticsGaps.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(error.message)}</p></div>`;
        questionAnalyticsUnresolved.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(error.message)}</p></div>`;
        questionAnalyticsHandoffs.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(error.message)}</p></div>`;
        questionAnalyticsDrafts.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(error.message)}</p></div>`;
        setInlineStatus(questionAnalyticsResponse, error.message, "error");
    }
}

function renderQuestionAnalyticsSummary(overview) {
    if (!questionAnalyticsSummary) {
        return;
    }

    const entries = [
        ["总问答", overview.total_exchanges || 0],
        ["已收反馈", overview.feedback_count || 0],
        ["点踩/未解决", overview.unresolved_count || 0],
        ["人工接管", overview.human_handoff_count || 0],
    ];
    questionAnalyticsSummary.innerHTML = entries
        .map(([label, value]) => `<span class="memory-profile-chip">${escapeHtml(label)} · ${escapeHtml(String(value))}</span>`)
        .join("");
}

function renderQuestionAnalyticsClusters(clusters) {
    if (!questionAnalyticsClusters) {
        return;
    }
    if (!Array.isArray(clusters) || !clusters.length) {
        questionAnalyticsClusters.innerHTML = '<div class="list-card"><p class="list-body">最近窗口内还没有形成高频问题聚类。</p></div>';
        return;
    }
    questionAnalyticsClusters.innerHTML = clusters
        .map(
            (cluster) => `
                <article class="list-card list-card-analytics list-card-analytics-cluster">
                    <h3>${escapeHtml(cluster.label)}</h3>
                    <p class="list-meta">${escapeHtml(cluster.interaction_domain_label)} | 频次 ${escapeHtml(String(cluster.count))}</p>
                    <p class="list-body">示例问题：${escapeHtml((cluster.sample_questions || []).join("；") || "暂无")}</p>
                    <div class="list-card-actions">
                        <span class="status-badge">未解决 ${escapeHtml(String(cluster.unresolved_count || 0))}</span>
                        <span class="status-badge">点踩 ${escapeHtml(String(cluster.negative_feedback_count || 0))}</span>
                        <span class="status-badge">转人工 ${escapeHtml(String(cluster.human_handoff_count || 0))}</span>
                    </div>
                </article>
            `
        )
        .join("");
}

function renderQuestionAnalyticsGaps(gaps) {
    if (!questionAnalyticsGaps) {
        return;
    }
    if (!Array.isArray(gaps) || !gaps.length) {
        questionAnalyticsGaps.innerHTML = '<div class="list-card"><p class="list-body">最近窗口内还没有明显的知识缺口建议。</p></div>';
        return;
    }
    questionAnalyticsGaps.innerHTML = gaps
        .map(
            (gap) => `
                <article class="list-card list-card-analytics list-card-analytics-gap">
                    <h3>${escapeHtml(gap.label)}</h3>
                    <p class="list-meta">原因：${escapeHtml(gap.reason)}</p>
                    <p class="list-body">建议动作：${escapeHtml(gap.suggested_action)}</p>
                    <p class="list-body analytics-secondary-copy">样例：${escapeHtml((gap.sample_questions || []).join("；") || "暂无")}</p>
                    <div class="list-card-actions">
                        <div class="inline-action-group">
                            <button type="button" class="ghost-button inline-action-button" data-gap-draft-create="${escapeHtml(gap.cluster_id)}">${gap.draft_id ? "刷新草稿" : "生成 FAQ 草稿"}</button>
                            ${gap.draft_id && gap.draft_status !== "published"
                    ? `<button type="button" class="primary-button inline-action-button" data-gap-draft-publish="${escapeHtml(gap.draft_id)}">发布到知识库</button>`
                    : ""}
                        </div>
                        ${gap.draft_status ? `<span class="status-badge ${gap.draft_status === "published" ? "status-badge-confirmed" : "status-badge-pending"}">${gap.draft_status === "published" ? "已发布" : "已生成草稿"}</span>` : ""}
                    </div>
                </article>
            `
        )
        .join("");
}

function renderQuestionAnalyticsUnresolved(items) {
    if (!questionAnalyticsUnresolved) {
        return;
    }
    if (!Array.isArray(items) || !items.length) {
        questionAnalyticsUnresolved.innerHTML = '<div class="list-card"><p class="list-body">当前没有新的未解决问题。</p></div>';
        return;
    }
    questionAnalyticsUnresolved.innerHTML = items
        .map(
            (item) => `
                <article class="list-card list-card-analytics list-card-analytics-unresolved">
                    <h3>${escapeHtml(item.question)}</h3>
                    <p class="list-meta">${escapeHtml(item.student_name)} | ${escapeHtml(item.interaction_domain_label)} | ${escapeHtml(formatDateTime(item.created_at))}</p>
                    <p class="list-body">${escapeHtml(item.issue_summary || "用户点踩但未补充具体说明。")}</p>
                    <div class="list-card-actions">
                        <span class="status-badge ${item.needs_human_followup ? "status-badge-handoff" : "status-badge-pending"}">${item.needs_human_followup ? "需要人工跟进" : "待补知识/策略"}</span>
                    </div>
                </article>
            `
        )
        .join("");
}

function renderQuestionAnalyticsHandoffs(items) {
    if (!questionAnalyticsHandoffs) {
        return;
    }
    if (!Array.isArray(items) || !items.length) {
        questionAnalyticsHandoffs.innerHTML = '<div class="list-card"><p class="list-body">最近还没有用户显式要求人工跟进。</p></div>';
        return;
    }
    questionAnalyticsHandoffs.innerHTML = items
        .map(
            (item) => `
                <article class="list-card list-card-analytics list-card-analytics-handoff">
                    <h3>${escapeHtml(item.category_label)}</h3>
                    <p class="list-meta">次数 ${escapeHtml(String(item.count))} | 占比 ${escapeHtml(formatPercentage(item.share || 0))}</p>
                    <p class="list-body">样例：${escapeHtml((item.sample_questions || []).join("；") || "暂无")}</p>
                </article>
            `
        )
        .join("");
}

function renderQuestionAnalyticsDrafts(drafts) {
    if (!questionAnalyticsDrafts) {
        return;
    }
    if (!Array.isArray(drafts) || !drafts.length) {
        questionAnalyticsDrafts.innerHTML = '<div class="list-card"><p class="list-body">当前还没有生成待补知识草稿。</p></div>';
        return;
    }
    questionAnalyticsDrafts.innerHTML = drafts
        .map(
            (draft) => `
                <article class="list-card list-card-analytics list-card-analytics-draft">
                    <h3>${escapeHtml(draft.title)}</h3>
                    <p class="list-meta">${escapeHtml(draft.label)} | ${escapeHtml(formatDateTime(draft.updated_at))}</p>
                    <p class="list-body">${escapeHtml(draft.suggested_action)}</p>
                    <div class="list-card-actions">
                        <div class="inline-action-group">
                            <button type="button" class="ghost-button inline-action-button" data-gap-draft-create="${escapeHtml(draft.cluster_id)}">刷新草稿</button>
                            ${draft.status !== "published"
                    ? `<button type="button" class="primary-button inline-action-button" data-gap-draft-publish="${escapeHtml(draft.draft_id)}">发布到知识库</button>`
                    : ""}
                        </div>
                        <span class="status-badge ${draft.status === "published" ? "status-badge-confirmed" : "status-badge-pending"}">${draft.status === "published" ? "已发布" : "草稿中"}</span>
                    </div>
                </article>
            `
        )
        .join("");
}

async function handleKnowledgeGapDraftAction(event) {
    if (!ensureAdminOnlyAccess({ responseElement: questionAnalyticsResponse })) {
        return;
    }
    const createButton = event.target.closest("[data-gap-draft-create]");
    const publishButton = event.target.closest("[data-gap-draft-publish]");
    if (!createButton && !publishButton) {
        return;
    }

    try {
        if (createButton) {
            const clusterId = createButton.dataset.gapDraftCreate;
            createButton.disabled = true;
            setInlineStatus(questionAnalyticsResponse, "正在生成知识草稿...", "empty");
            await apiRequest("/analytics/questions/gap-drafts", {
                method: "POST",
                body: JSON.stringify({ cluster_id: clusterId, days: Number(questionAnalyticsWindow?.value || 7) }),
            });
            setInlineStatus(questionAnalyticsResponse, "知识草稿已生成，可继续发布到知识库。", "success");
            await loadQuestionAnalytics();
            return;
        }

        if (publishButton) {
            const draftId = publishButton.dataset.gapDraftPublish;
            publishButton.disabled = true;
            setInlineStatus(questionAnalyticsResponse, "正在发布知识草稿到知识库...", "empty");
            await apiRequest(`/analytics/questions/gap-drafts/${encodeURIComponent(draftId)}/publish`, {
                method: "POST",
            });
            setInlineStatus(questionAnalyticsResponse, "知识草稿已发布到知识库。", "success");
            await refreshStatus();
            await loadQuestionAnalytics();
        }
    } catch (error) {
        setInlineStatus(questionAnalyticsResponse, error.message, "error");
    }
}

async function loadEscalationList() {
    if (!ensureAdminOnlyAccess({ responseElement: escalationAdminResponse })) {
        return;
    }
    const selectedStatus = escalationStatusFilter?.value ?? "待处理";
    const selectedRoute = escalationRouteFilter?.value ?? "";
    const statusLabel = selectedStatus || "全部状态";
    setInlineStatus(escalationAdminResponse, `正在加载${statusLabel}人工请求...`, "empty");
    escalationList.innerHTML = `<div class="list-card"><p class="list-body">正在加载${escapeHtml(statusLabel)}人工请求...</p></div>`;

    const params = new URLSearchParams();
    if (selectedStatus) {
        params.set("status", selectedStatus);
    }
    if (selectedRoute) {
        params.set("route", selectedRoute);
    }

    try {
        const suffix = params.toString() ? `?${params.toString()}` : "";
        const records = await apiRequest(`/escalations${suffix}`);
        escalationList.innerHTML = "";
        if (!records.length) {
            escalationList.innerHTML = `<div class="list-card"><p class="list-body">当前没有${escapeHtml(statusLabel)}人工请求。</p></div>`;
            setInlineStatus(escalationAdminResponse, `当前没有${statusLabel}人工请求。`, "success");
            return;
        }

        records.forEach((record) => {
            const card = document.createElement("article");
            card.className = `list-card list-card-escalation ${record.status === "待处理" ? "list-card-escalation-pending" : "list-card-escalation-resolved"}`;
            const isPending = record.status === "待处理";
            const reasonHtml = record.reason
                ? `<p class="list-body booking-reason-copy">升级原因：${escapeHtml(record.reason)}</p>`
                : "";
            const resolutionHtml = record.resolution_note
                ? `<p class="list-body booking-reason-copy">处理备注：${escapeHtml(record.resolution_note)}</p>`
                : "";
            const actionsHtml = isPending
                ? `
                    <div class="booking-reason-field">
                        <label>
                            <span>处理备注</span>
                            <textarea rows="2" placeholder="例如：已转老师本人处理。" data-escalation-resolution-note="${escapeHtml(record.escalation_id)}"></textarea>
                        </label>
                    </div>
                    <div class="inline-action-group">
                        <button type="button" class="primary-button inline-action-button" data-escalation-resolve="${escapeHtml(record.escalation_id)}">标记已处理</button>
                    </div>
                `
                : "";
            card.innerHTML = `
                <h3>${escapeHtml(formatEscalationRouteLabel(record.route))}</h3>
                <p class="list-meta">${escapeHtml(record.student_name)} | ${escapeHtml(record.student_email || "未提供邮箱")}</p>
                <p class="list-body">${escapeHtml(record.question)}</p>
                ${reasonHtml}
                ${resolutionHtml}
                <div class="list-card-actions">
                    <div class="inline-action-group">
                        <span class="status-badge ${escapeHtml(statusBadgeClassName(record.status))}">${escapeHtml(record.status)}</span>
                        <span class="status-badge ${escapeHtml(escalationRouteBadgeClassName(record.route))}">${escapeHtml(formatEscalationRouteLabel(record.route))}</span>
                    </div>
                    ${actionsHtml}
                </div>
            `;
            escalationList.appendChild(card);
        });
        setInlineStatus(escalationAdminResponse, `共有 ${records.length} 条${statusLabel}人工请求。`, "empty");
    } catch (error) {
        escalationList.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(error.message)}</p></div>`;
        setInlineStatus(escalationAdminResponse, error.message, "error");
    }
}

function syncMemoryProfileCategoryOptions(categories) {
    if (!memoryProfilesCategoryFilter) {
        return;
    }

    const previousValue = memoryProfilesCategoryFilter.value;
    const normalizedCategories = [...new Set((categories || []).filter(Boolean))];
    memoryProfilesCategoryFilter.innerHTML = [
        '<option value="">全部类别</option>',
        ...normalizedCategories.map(
            (category) =>
                `<option value="${escapeHtml(category)}">${escapeHtml(formatProfileCategoryLabel(category))}</option>`
        ),
    ].join("");
    memoryProfilesCategoryFilter.value = normalizedCategories.includes(previousValue) ? previousValue : "";
}

function renderMemoryProfileSummary(categoryCounts) {
    if (!memoryProfilesSummary) {
        return;
    }

    const entries = Object.entries(categoryCounts || {}).sort((left, right) => right[1] - left[1]);
    if (!entries.length) {
        memoryProfilesSummary.innerHTML = "";
        return;
    }

    memoryProfilesSummary.innerHTML = entries
        .map(
            ([category, count]) =>
                `<span class="memory-profile-chip">${escapeHtml(formatProfileCategoryLabel(category))} · ${escapeHtml(String(count))}</span>`
        )
        .join("");
}

async function loadAvailabilityEditor() {
    if (!ensureAdminOnlyAccess({ responseElement: availabilityResponse })) {
        return;
    }
    setInlineStatus(availabilityResponse, "正在加载本周可预约时段...", "empty");
    try {
        const schedule = await apiRequest("/availability");
        availabilityEditorState = normalizeAvailabilityState(schedule);
        renderAvailabilityEditor();
        setInlineStatus(availabilityResponse, "直接点格子就行，改完记得保存。", "empty");
    } catch (error) {
        availabilityGrid.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(error.message)}</p></div>`;
        setInlineStatus(availabilityResponse, error.message, "error");
    }
}

function renderAvailabilityEditor() {
    if (!availabilityEditorState) {
        availabilityGrid.innerHTML = "";
        return;
    }

    const weekDates = getWeekDates(availabilityEditorState.weekOf);
    availabilityWeekLabel.textContent = `${weekDates[0].iso} 至 ${weekDates[weekDates.length - 1].iso} · ${availabilityEditorState.timezone}`;
    availabilityGrid.innerHTML = weekDates
        .map((day) => {
            const slots = buildAvailabilitySlots()
                .map((slot) => {
                    const selected = availabilityEditorState.selectedSlots.has(`${day.iso}|${slot}`);
                    return `
                        <button
                            type="button"
                            class="availability-slot-button ${selected ? "availability-slot-selected" : ""}"
                            data-availability-date="${day.iso}"
                            data-availability-slot="${slot}"
                            aria-pressed="${selected ? "true" : "false"}"
                        >${slot}</button>
                    `;
                })
                .join("");
            const note = availabilityEditorState.dayNotes.get(day.iso);
            return `
                <section class="availability-day-card">
                    <div class="availability-day-head">
                        <h3>${escapeHtml(day.label)}</h3>
                        <p>${escapeHtml(day.iso)}</p>
                    </div>
                    ${note ? `<p class="availability-day-note">${escapeHtml(note)}</p>` : ""}
                    <div class="availability-slot-grid">${slots}</div>
                </section>
            `;
        })
        .join("");
}

function handleAvailabilityGridClick(event) {
    const button = event.target.closest("[data-availability-date][data-availability-slot]");
    if (!button || !availabilityEditorState) {
        return;
    }
    const key = `${button.dataset.availabilityDate}|${button.dataset.availabilitySlot}`;
    if (availabilityEditorState.selectedSlots.has(key)) {
        availabilityEditorState.selectedSlots.delete(key);
        button.classList.remove("availability-slot-selected");
        button.setAttribute("aria-pressed", "false");
    } else {
        availabilityEditorState.selectedSlots.add(key);
        button.classList.add("availability-slot-selected");
        button.setAttribute("aria-pressed", "true");
    }
}

function clearAvailabilityEditor() {
    if (!availabilityEditorState) {
        return;
    }
    availabilityEditorState.selectedSlots.clear();
    renderAvailabilityEditor();
    setInlineStatus(availabilityResponse, "已清空当前填涂，请记得保存。", "empty");
}

function applyAvailabilityTemplate(templateName) {
    if (!availabilityEditorState) {
        return;
    }

    const weekDates = getWeekDates(availabilityEditorState.weekOf);
    const nextSlots = new Set();
    weekDates.forEach((day, index) => {
        if (index >= 5) {
            return;
        }

        const slots = templateName === "workday-full"
            ? buildSlotsForWindow("09:00", "18:00")
            : templateName === "workday-morning"
                ? buildSlotsForWindow("09:00", "12:00")
                : buildSlotsForWindow("14:00", "18:00");
        slots.forEach((slot) => nextSlots.add(`${day.iso}|${slot}`));
    });
    availabilityEditorState.selectedSlots = nextSlots;
    renderAvailabilityEditor();
    setInlineStatus(
        availabilityResponse,
        templateName === "workday-full"
            ? "已应用工作日全天模板，请检查后保存。"
            : templateName === "workday-morning"
                ? "已应用工作日上午模板，请检查后保存。"
                : "已应用工作日下午模板，请检查后保存。",
        "empty"
    );
}

async function copyPreviousWeekTemplate() {
    if (!ensureAdminOnlyAccess({ responseElement: availabilityResponse })) {
        return;
    }
    if (!availabilityEditorState) {
        return;
    }

    setInlineStatus(availabilityResponse, "正在复制上周安排...", "empty");
    try {
        const template = await apiRequest(`/availability/previous-week?week_of=${encodeURIComponent(availabilityEditorState.weekOf)}`);
        if (!Array.isArray(template.days) || !template.days.length) {
            setInlineStatus(availabilityResponse, "没有找到可复制的上周安排。", "error");
            return;
        }
        availabilityEditorState = normalizeAvailabilityState(template);
        renderAvailabilityEditor();
        setInlineStatus(availabilityResponse, "已复制上周安排，请检查后保存。", "success");
    } catch (error) {
        setInlineStatus(availabilityResponse, error.message, "error");
    }
}

async function saveAvailabilityEditor() {
    if (!ensureAdminOnlyAccess({ responseElement: availabilityResponse })) {
        return;
    }
    if (!availabilityEditorState) {
        return;
    }
    setInlineStatus(availabilityResponse, "正在保存本周可预约时段...", "empty");
    try {
        const payload = buildAvailabilityPayload(availabilityEditorState);
        const saved = await apiRequest("/availability", {
            method: "PUT",
            body: JSON.stringify(payload),
        });
        availabilityEditorState = normalizeAvailabilityState(saved);
        renderAvailabilityEditor();
        setInlineStatus(availabilityResponse, "本周可预约时段已保存。", "success");
    } catch (error) {
        setInlineStatus(availabilityResponse, error.message, "error");
    }
}

async function handleBookingApprovalClick(event) {
    if (!ensureAdminOnlyAccess({ responseElement: bookingAdminResponse })) {
        return;
    }
    const button = event.target.closest("[data-booking-confirm], [data-booking-reject]");
    if (!button) {
        return;
    }
    const bookingId = button.dataset.bookingConfirm || button.dataset.bookingReject;
    const action = button.dataset.bookingConfirm ? "confirm" : "reject";
    const rejectionReasonField = button
        .closest(".list-card")
        ?.querySelector(`[data-booking-rejection-reason="${CSS.escape(bookingId)}"]`);
    const rejectionReason = typeof rejectionReasonField?.value === "string" ? rejectionReasonField.value.trim() : "";
    button.disabled = true;
    button.textContent = action === "confirm" ? "确认中..." : "拒绝中...";
    setInlineStatus(bookingAdminResponse, action === "confirm" ? "正在确认预约..." : "正在退回这条预约申请...", "empty");
    try {
        const result = await apiRequest(`/bookings/${encodeURIComponent(bookingId)}/${action}`, {
            method: "POST",
            body: JSON.stringify(action === "reject" ? { rejection_reason: rejectionReason || null } : {}),
        });
        renderBookingResponseStatus(bookingAdminResponse, result, {
            state: result.accepted ? "success" : "error",
            lines: result.booking ? [`${result.booking.student_name} 的申请当前状态为 ${result.booking.status}。`] : [],
        });
        await loadBookingList();
    } catch (error) {
        setInlineStatus(bookingAdminResponse, error.message, "error");
        button.disabled = false;
        button.textContent = action === "confirm" ? "确认预约" : "拒绝预约";
    }
}

async function handleEscalationResolveClick(event) {
    if (!ensureAdminOnlyAccess({ responseElement: escalationAdminResponse })) {
        return;
    }
    const button = event.target.closest("[data-escalation-resolve]");
    if (!button) {
        return;
    }
    const escalationId = button.dataset.escalationResolve;
    const resolutionNoteField = button
        .closest(".list-card")
        ?.querySelector(`[data-escalation-resolution-note="${CSS.escape(escalationId)}"]`);
    const resolutionNote = typeof resolutionNoteField?.value === "string" ? resolutionNoteField.value.trim() : "";
    button.disabled = true;
    button.textContent = "处理中...";
    setInlineStatus(escalationAdminResponse, "正在更新人工处理请求...", "empty");
    try {
        const result = await apiRequest(`/escalations/${encodeURIComponent(escalationId)}/resolve`, {
            method: "POST",
            body: JSON.stringify({ resolution_note: resolutionNote || null }),
        });
        setInlineStatus(
            escalationAdminResponse,
            `${formatEscalationRouteLabel(result.route)}已更新为${result.status}。`,
            "success"
        );
        await loadEscalationList();
    } catch (error) {
        setInlineStatus(escalationAdminResponse, error.message, "error");
        button.disabled = false;
        button.textContent = "标记已处理";
    }
}

function statusBadgeClassName(status) {
    switch (status) {
        case "已确认":
            return "status-badge-confirmed";
        case "已拒绝":
            return "status-badge-rejected";
        case "已处理":
            return "status-badge-confirmed";
        default:
            return "status-badge-pending";
    }
}

function escalationRouteBadgeClassName(route) {
    switch (route) {
        case "human_handoff":
            return "status-badge-handoff";
        default:
            return "status-badge-review";
    }
}

function formatEscalationRouteLabel(route) {
    return route === "human_handoff" ? "必须转人工" : "待审核";
}

function isLocalHostname(hostname) {
    return hostname === "localhost" || hostname === "127.0.0.1";
}

function normalizeOrigin(origin) {
    return origin ? origin.replace(/\/$/, "") : "";
}

function buildApiUrl(path, origin = "") {
    if (/^https?:\/\//.test(path)) {
        return path;
    }
    if (!origin) {
        return path;
    }
    return new URL(path, `${normalizeOrigin(origin)}/`).toString();
}

function getApiOriginCandidates() {
    const candidates = [];
    const pushCandidate = (value) => {
        const normalized = normalizeOrigin(value);
        if (!normalized || candidates.includes(normalized)) {
            return;
        }
        candidates.push(normalized);
    };

    if (resolvedApiOrigin) {
        pushCandidate(resolvedApiOrigin);
    }

    if (globalThis.location?.origin) {
        pushCandidate(globalThis.location.origin);
    }

    const hostname = globalThis.location?.hostname || "";
    const protocol = globalThis.location?.protocol || "http:";
    const currentPort = globalThis.location?.port || "";
    if (isLocalHostname(hostname)) {
        const hostnames = hostname === "localhost" ? ["localhost", "127.0.0.1"] : ["127.0.0.1", "localhost"];
        for (const localHostname of hostnames) {
            if (currentPort) {
                pushCandidate(`${protocol}//${localHostname}:${currentPort}`);
            }
            for (const port of LOCAL_API_PORT_CANDIDATES) {
                pushCandidate(`${protocol}//${localHostname}:${port}`);
            }
        }
    }

    return candidates;
}

async function probeApiOrigin(origin) {
    const url = buildApiUrl("/auth/user/session", origin);
    try {
        const response = await fetch(url, {
            method: "GET",
            credentials: "include",
            headers: {
                "Accept": "application/json",
            },
        });
        if (!response.ok) {
            return false;
        }
        const payload = await response.json();
        return typeof payload?.is_authenticated === "boolean" && typeof payload?.mode === "string";
    } catch {
        return false;
    }
}

async function resolveApiOrigin() {
    if (resolvedApiOrigin) {
        return resolvedApiOrigin;
    }
    if (apiOriginResolutionPromise) {
        return apiOriginResolutionPromise;
    }

    apiOriginResolutionPromise = (async () => {
        for (const candidate of getApiOriginCandidates()) {
            if (await probeApiOrigin(candidate)) {
                resolvedApiOrigin = candidate;
                return resolvedApiOrigin;
            }
        }
        resolvedApiOrigin = normalizeOrigin(globalThis.location?.origin || "");
        return resolvedApiOrigin;
    })();

    try {
        return await apiOriginResolutionPromise;
    } finally {
        apiOriginResolutionPromise = null;
    }
}

async function apiRequest(path, options = {}) {
    const { timeoutMs = 15000, ...fetchOptions } = options;
    const controller = new AbortController();
    const timeoutId = globalThis.setTimeout(() => controller.abort(), timeoutMs);
    const apiOrigin = await resolveApiOrigin();
    const requestUrl = buildApiUrl(path, apiOrigin);

    let response;
    try {
        response = await fetch(requestUrl, {
            headers: {
                "Content-Type": "application/json",
                ...(fetchOptions.headers || {}),
            },
            credentials: "include",
            ...fetchOptions,
            signal: controller.signal,
        });
    } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
            throw new Error("请求超时，请稍后重试。", { cause: error });
        }
        throw new Error("当前无法连接服务，请确认页面后端已经启动。", { cause: error });
    } finally {
        globalThis.clearTimeout(timeoutId);
    }

    if (!response.ok) {
        const text = await response.text();
        throw new Error(`请求失败（${response.status}）：${text}`);
    }

    return response.json();
}

function setResponse(element, text, state) {
    element.textContent = text;
    element.className = `response-card response-${state}`;
}

function setInlineStatus(element, text, state) {
    element.textContent = text;
    element.className = `inline-status inline-status-${state}`;
}

function renderBookingResponseStatus(element, bookingResponse, options = {}) {
    const { state = "empty", lines = [] } = options;
    const notification = bookingResponse?.notification || null;
    const message = stripNotificationText(bookingResponse?.message || "", notification);
    const summaryLines = [message, ...lines].filter(Boolean);
    element.innerHTML = `
        <div class="inline-status-copy">
            ${summaryLines.map((line) => `<p class="inline-status-line">${escapeHtml(line)}</p>`).join("")}
        </div>
        ${buildNotificationStatusHtml(notification, { title: "邮件通知状态" })}
    `;
    element.className = `inline-status inline-status-${state}`;
}

function appendMessage(role, label, text, options = {}) {
    const article = document.createElement("article");
    const stateClass = options.state ? ` message-${options.state}` : "";
    const emphasisClass = options.emphasis ? ` message-emphasis-${options.emphasis}` : "";
    article.className = `message message-${role}${stateClass}${emphasisClass}`;
    article.innerHTML = `
    <div class="message-role">${escapeHtml(label)}</div>
    <div class="message-frame">
        <div class="message-body">${escapeHtml(text)}</div>
    </div>
  `;
    chatStream.appendChild(article);
    chatStream.scrollTop = chatStream.scrollHeight;
    return article;
}

function renderAssistantMessage(
    container,
    text,
    basisItems,
    followUpActions,
    hits,
    bookingResult = null,
    isError = false,
    exchangeId = null
) {
    const bodyClass = isError ? "message-body" : "message-body";
    const cleanedText = stripNotificationText(text, bookingResult?.notification || null);
    container.classList.remove("message-pending");
    container.classList.add("message-ready");
    const notificationHtml = buildNotificationStatusHtml(bookingResult?.notification || null, { title: "邮件通知状态" });
    const basisHtml = Array.isArray(basisItems) && basisItems.length
        ? buildCollapsibleSupportSectionHtml({
            kicker: "Support",
            title: "本次回答依据",
            copy: "下面这些信息说明这条回复主要依据了哪些材料或记录。",
            count: basisItems.length,
            contentHtml: `
                <div class="message-basis-list">
                    ${basisItems.map((item) => buildAnswerBasisItemHtml(item)).join("")}
                </div>
            `,
        })
        : hits.length
            ? buildCollapsibleSupportSectionHtml({
                kicker: "Knowledge",
                title: "相关知识",
                copy: "这些知识条目是本次回答优先参考的资料。",
                count: hits.length,
                contentHtml: `
                    <div class="message-knowledge-list">
                        ${hits
                        .map(
                            (hit) => `
                                    <div class="message-knowledge-item">
                                        <strong>${escapeHtml(hit.title)}</strong>
                                        ${hit.source_name ? `<span>${escapeHtml(hit.source_name)}</span>` : ""}
                                    </div>
                                `
                        )
                        .join("")}
                    </div>
                `,
            })
            : "";
    const followUpHtml = Array.isArray(followUpActions) && followUpActions.length
        ? buildCollapsibleSupportSectionHtml({
            kicker: "Next",
            title: "建议的后续动作",
            copy: "这些动作会把这次对话继续往后推进，而不是停在一条回复上。",
            count: followUpActions.length,
            sectionClassName: "message-section-follow-up",
            contentHtml: `
                <div class="message-basis-list">
                    ${followUpActions.map((action) => buildFollowUpActionHtml(action)).join("")}
                </div>
            `,
        })
        : "";
    container.innerHTML = `
        <div class="message-role">${escapeHtml(assistantLabel)}</div>
    <div class="message-frame">
        <div class="message-main-copy">
            <span class="message-section-kicker">Reply</span>
            <div class="${bodyClass}">${escapeHtml(cleanedText)}</div>
        </div>
        ${notificationHtml}
        ${basisHtml}
        ${followUpHtml}
        ${buildFeedbackSectionHtml(exchangeId, isError)}
    </div>
  `;
    if (isError) {
        container.style.background = "var(--error)";
    }
    if (exchangeId && !isError) {
        attachFeedbackHandlers(container, exchangeId);
    }
    chatStream.scrollTop = chatStream.scrollHeight;
}

function buildCollapsibleSupportSectionHtml({ kicker, title, copy, count, contentHtml, sectionClassName = "message-section-support" }) {
    const countLabel = Number.isFinite(count) ? `${count} 条` : "查看";
    return `
        <section class="message-section ${escapeHtml(sectionClassName)}" data-expanded="false">
            <button type="button" class="message-section-toggle" aria-expanded="false">
                <div class="message-section-toggle-copy">
                    <span class="message-section-kicker">${escapeHtml(kicker)}</span>
                    <strong class="message-section-title">${escapeHtml(title)}</strong>
                </div>
                <div class="message-section-toggle-meta">
                    <span class="message-section-count">${escapeHtml(countLabel)}</span>
                    <span class="message-section-chevron">查看</span>
                </div>
            </button>
            <div class="message-section-content" hidden>
                <div class="message-basis-header">
                    <p class="message-basis-copy">${escapeHtml(copy)}</p>
                </div>
                ${contentHtml}
            </div>
        </section>
    `;
}

function stripNotificationText(text, notification) {
    if (!notification || !text) {
        return text;
    }

    let cleaned = String(text);
    [notification.summary, notification.detail].forEach((fragment) => {
        if (fragment) {
            cleaned = cleaned.replace(fragment, "");
        }
    });

    cleaned = cleaned
        .replace(/[ \t]+\n/g, "\n")
        .replace(/\n{3,}/g, "\n\n")
        .replace(/[ \t]{2,}/g, " ")
        .trim();

    return cleaned || String(text).trim();
}

function buildNotificationStatusHtml(notification, options = {}) {
    if (!notification) {
        return "";
    }

    const { title = "通知状态" } = options;
    const statusLabel = notification.status === "sent"
        ? "已发送"
        : notification.status === "failed"
            ? "发送失败"
            : "未发送";
    const statusClass = notification.status === "sent"
        ? "notification-card-sent"
        : notification.status === "failed"
            ? "notification-card-failed"
            : "notification-card-skipped";

    return `
        <section class="notification-card ${statusClass}">
            <div class="notification-card-head">
                <strong class="notification-card-title">${escapeHtml(title)}</strong>
                <span class="notification-card-badge">${escapeHtml(statusLabel)}</span>
            </div>
            <p class="notification-card-summary">${escapeHtml(notification.summary)}</p>
            ${notification.recipient ? `<p class="notification-card-meta">收件人：${escapeHtml(notification.recipient)}</p>` : ""}
            ${notification.detail ? `<p class="notification-card-detail">${escapeHtml(notification.detail)}</p>` : ""}
        </section>
    `;
}

function buildFollowUpActionHtml(action) {
    const card = formatFollowUpActionCard(action);
    const detailHtml = card.checklistItems?.length
        ? `
            <ul class="message-basis-checklist">
                ${card.checklistItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
            </ul>
        `
        : `<p class="message-basis-detail">${escapeHtml(card.detail)}</p>`;
    return `
        <article class="message-basis-item">
            <div class="message-basis-head">
                <span class="message-basis-tag">${escapeHtml(card.label)}</span>
                ${card.badge ? `<span class="message-basis-source">${escapeHtml(card.badge)}</span>` : ""}
            </div>
            <p class="message-basis-title">${escapeHtml(card.title)}</p>
            ${detailHtml}
            ${card.note ? `<p class="message-basis-meta">${escapeHtml(card.note)}</p>` : ""}
        </article>
    `;
}

function buildAnswerBasisItemHtml(item) {
    const card = formatAnswerBasisCard(item);
    return `
        <article class="message-basis-item">
            <div class="message-basis-head">
                <span class="message-basis-tag">${escapeHtml(card.label)}</span>
                ${card.badge ? `<span class="message-basis-source">${escapeHtml(card.badge)}</span>` : ""}
            </div>
            <p class="message-basis-title">${escapeHtml(card.title)}</p>
            ${card.detail ? `<p class="message-basis-detail">${escapeHtml(card.detail)}</p>` : ""}
        </article>
    `;
}

function formatAnswerBasisCard(item) {
    return {
        label: item.basis_label || "回答依据",
        badge: cleanAnswerBasisSource(item.source_label),
        title: cleanAnswerBasisTitle(item.title),
        detail: cleanAnswerBasisDetail(item.detail, item.title),
    };
}

function formatFollowUpActionCard(action) {
    const label = formatFollowUpActionLabel(action.action_type);
    const title = formatFollowUpActionTitle(action);
    const detail = formatFollowUpActionDetail(action);
    const note = formatFollowUpActionNote(action);
    const checklistItems = action.action_type === "todo_review" ? buildTodoChecklistItems(detail) : [];
    const badge = action.channel === "email" ? "系统邮件" : "聊天内提醒";
    return { label, title, detail, note, badge, checklistItems };
}

function formatFollowUpActionTitle(action) {
    switch (action.action_type) {
        case "recommended_reading":
            return `先看这条材料：${cleanFollowUpTitle(action.title)}`;
        case "todo_review":
            return "先把开会前要准备的材料列出来";
        case "office_hour_recommendation":
            return "如果还要继续聊，下一步就去预约时间";
        case "course_resource_recommendation":
            return `继续自学这条材料：${cleanFollowUpTitle(action.title)}`;
        case "post_meeting_summary":
            return "会后系统会自动发总结邮件";
        default:
            return cleanFollowUpTitle(action.title);
    }
}

function formatFollowUpActionDetail(action) {
    const detail = cleanFollowUpDetail(action.detail);
    switch (action.action_type) {
        case "recommended_reading": {
            const excerpt = extractFollowUpExcerpt(detail);
            return excerpt
                ? `重点先看：${excerpt}`
                : "这条材料和你当前的问题最相关，建议先读完再继续追问更具体的问题。";
        }
        case "todo_review": {
            const checklist = detail.replace(/^建议回顾[:：]\s*/, "");
            return checklist || "agenda、当前 blocker、已有 draft/结果、最想确认的问题。";
        }
        case "office_hour_recommendation":
            return detail || "如果你还需要深入沟通，建议尽早查看 office hour 或本周开放预约时段。";
        case "course_resource_recommendation":
            return detail || "先把相关课程材料过一遍，再带着具体问题回来继续问。";
        case "post_meeting_summary":
            return detail || "系统会在会后自动整理本次沟通的重点和后续事项。";
        default:
            return detail || "建议继续推进这一步。";
    }
}

function formatFollowUpActionNote(action) {
    if (action.due_at) {
        return `预计时间：${formatDateTime(action.due_at)}`;
    }

    switch (action.action_type) {
        case "recommended_reading":
            return "读完后再继续提问，回复会更具体。";
        case "todo_review":
            return "准备到位后再预约，会更高效。";
        case "office_hour_recommendation":
            return "适合你已经准备好问题、需要深入沟通的时候。";
        case "course_resource_recommendation":
            return "适合先自学一轮，再带着卡点回来追问。";
        default:
            return "";
    }
}

function cleanFollowUpTitle(title) {
    const normalized = String(title || "")
        .replace(/^(推荐阅读|课程资源推荐|先看|继续看)[：:]/, "")
        .replace(/\s+/g, " ")
        .trim();
    if (!normalized) {
        return "相关材料";
    }

    const parts = normalized
        .split(/[|｜]/)
        .map((item) => item.trim())
        .filter((item) => item && !looksLikeFragmentedFollowUpTitle(item));
    const compact = parts.length ? parts.slice(0, 2).join(" · ") : normalized;
    return compact.slice(0, 80);
}

function looksLikeFragmentedFollowUpTitle(value) {
    const pieces = value
        .split("/")
        .map((item) => item.trim())
        .filter(Boolean);
    return pieces.length >= 2 && pieces.every((item) => item.length <= 3);
}

function cleanFollowUpDetail(detail) {
    return String(detail || "")
        .replace(/\s+/g, " ")
        .replace(/；/g, "；")
        .trim();
}

function extractFollowUpExcerpt(detail) {
    const matched = detail.match(/(?:最相关，建议先看这一部分[:：]|关联内容[:：])(.*)$/);
    if (!matched) {
        return detail.slice(0, 140);
    }
    return matched[1].trim().slice(0, 140);
}

function buildTodoChecklistItems(detail) {
    const normalized = String(detail || "").replace(/^建议回顾[:：]\s*/, "").trim();
    if (!normalized) {
        return [];
    }
    return normalized
        .split("；")
        .map((item) => item.trim())
        .filter(Boolean)
        .slice(0, 5);
}

function cleanAnswerBasisTitle(title) {
    const normalized = cleanFollowUpTitle(title);
    return normalized || "相关依据";
}

function cleanAnswerBasisSource(sourceLabel) {
    const normalized = String(sourceLabel || "").trim();
    return normalized.replace(/^来源[:：]\s*/, "");
}

function cleanAnswerBasisDetail(detail, title) {
    const normalized = cleanFollowUpDetail(detail);
    const titleText = String(title || "").trim();
    if (!normalized || normalized === titleText) {
        return "";
    }
    return normalized;
}

function buildFeedbackSectionHtml(exchangeId, isError) {
    if (!exchangeId || isError) {
        return "";
    }
    const alreadySubmitted = submittedFeedbackExchangeIds.has(exchangeId);
    return `
        <div class="message-feedback" data-feedback-exchange="${escapeHtml(exchangeId)}">
            <div class="message-feedback-actions">
                <button type="button" class="ghost-button message-feedback-button" data-feedback-up ${alreadySubmitted ? "disabled" : ""}>有帮助</button>
                <button type="button" class="ghost-button message-feedback-button" data-feedback-down ${alreadySubmitted ? "disabled" : ""}>没答好</button>
                <span class="message-feedback-status">${alreadySubmitted ? "已提交反馈。" : "这条回答有帮助吗？"}</span>
            </div>
            <div class="message-feedback-form hidden">
                <textarea rows="3" class="message-feedback-textarea" placeholder="例如：没答到哪一点、缺了哪类资料、建议补什么。"></textarea>
                <label class="message-feedback-checkbox">
                    <input type="checkbox" class="message-feedback-handoff" />
                    <span>建议人工跟进</span>
                </label>
                <div class="inline-action-group">
                    <button type="button" class="primary-button inline-action-button" data-feedback-submit>提交点踩</button>
                    <button type="button" class="ghost-button inline-action-button" data-feedback-cancel>取消</button>
                </div>
            </div>
        </div>
    `;
}

function attachFeedbackHandlers(container, exchangeId) {
    const upButton = container.querySelector("[data-feedback-up]");
    const downButton = container.querySelector("[data-feedback-down]");
    const submitButton = container.querySelector("[data-feedback-submit]");
    const cancelButton = container.querySelector("[data-feedback-cancel]");
    const form = container.querySelector(".message-feedback-form");
    const status = container.querySelector(".message-feedback-status");
    const textarea = container.querySelector(".message-feedback-textarea");
    const handoff = container.querySelector(".message-feedback-handoff");

    if (!upButton || !downButton || !status) {
        return;
    }

    upButton.addEventListener("click", async () => {
        await submitFeedbackExchange(
            exchangeId,
            { rating: "up" },
            { container, status, form, upButton, downButton, submittedMessage: "已记录为有帮助。" }
        );
    });

    downButton.addEventListener("click", () => {
        form?.classList.remove("hidden");
        status.textContent = "告诉我哪里没答好，管理员周报会据此补资料和调策略。";
        textarea?.focus();
    });

    cancelButton?.addEventListener("click", () => {
        form?.classList.add("hidden");
        status.textContent = "这条回答有帮助吗？";
    });

    submitButton?.addEventListener("click", async () => {
        await submitFeedbackExchange(
            exchangeId,
            {
                rating: "down",
                resolved: false,
                issue_summary: textarea?.value?.trim() || null,
                needs_human_followup: Boolean(handoff?.checked),
            },
            {
                container,
                status,
                form,
                upButton,
                downButton,
                submittedMessage: handoff?.checked ? "已记录点踩，并标记需要人工跟进。" : "已记录点踩，后续会进入管理员周报。"
            }
        );
    });
}

async function submitFeedbackExchange(exchangeId, payload, ui) {
    try {
        ui.status.textContent = "正在提交反馈...";
        const response = await apiRequest("/chat/feedback", {
            method: "POST",
            body: JSON.stringify({ exchange_id: exchangeId, ...payload }),
        });
        submittedFeedbackExchangeIds.add(response.exchange_id);
        ui.status.textContent = ui.submittedMessage;
        ui.upButton.disabled = true;
        ui.downButton.disabled = true;
        ui.form?.classList.add("hidden");
    } catch (error) {
        ui.status.textContent = error.message;
    }
}

function renderWorkflowTrace(steps, meta = {}) {
    if (!workflowTrace) {
        return;
    }
    const resolvedMeta = {
        workflowAction:
            meta.workflowAction !== undefined ? meta.workflowAction : latestWorkflowMeta.workflowAction,
        knowledgeHits:
            meta.knowledgeHits !== undefined ? meta.knowledgeHits : latestWorkflowMeta.knowledgeHits,
        isStreaming: meta.isStreaming !== undefined ? meta.isStreaming : latestWorkflowMeta.isStreaming,
        currentLabel: meta.currentLabel !== undefined ? meta.currentLabel : latestWorkflowMeta.currentLabel,
    };
    latestWorkflowMeta = resolvedMeta;

    if (!steps.length) {
        updateWorkflowStats([], resolvedMeta);
        workflowTrace.innerHTML = `
            <article class="workflow-step workflow-step-empty" data-expanded="false">
                <button type="button" class="workflow-step-toggle" aria-expanded="false">
                    <div class="workflow-step-header">
                        <span class="workflow-step-index">-</span>
                        <div class="workflow-step-content">
                            <div class="workflow-step-meta">
                                <h3 class="workflow-step-title">等待你的第一条问题</h3>
                                <span class="workflow-step-chevron">展开</span>
                            </div>
                                <p class="workflow-step-summary">发出消息后，这里会像现场记录板一样按顺序展开检索、判断和回复生成过程。</p>
                        </div>
                    </div>
                </button>
                    <div class="workflow-step-detail" hidden>这里会记录系统先看了什么资料、做了哪些判断，以及最后如何组织出回复。</div>
            </article>
        `;
        return;
    }

    updateWorkflowStats(steps, resolvedMeta);

    workflowTrace.innerHTML = steps
        .map((step, index) => {
            const status = step.status || "completed";
            const statusLabel = workflowStatusLabel(status);
            const detail = step.detail || "";
            const summary = step.summary || summarizeWorkflowDetail(detail);
            const expanded = status === "active" || status === "error";
            const isCurrent = resolvedMeta.isStreaming && index === steps.length - 1;
            const cardClasses = [
                "workflow-step",
                `workflow-step-${escapeHtml(status)}`,
                status === "completed" ? "workflow-step-completed" : "",
                isCurrent ? "workflow-step-current" : "",
            ]
                .filter(Boolean)
                .join(" ");
            const durationBadge =
                typeof step.duration_ms === "number"
                    ? `<span class="workflow-step-duration">${escapeHtml(formatWorkflowDuration(step.duration_ms))}</span>`
                    : "";
            const currentBadge = isCurrent
                ? '<span class="workflow-step-status workflow-step-status-active">当前</span>'
                : "";
            return `
                <article class="${cardClasses}" data-expanded="${expanded}">
                    <button type="button" class="workflow-step-toggle" aria-expanded="${expanded}">
                        <div class="workflow-step-header">
                            <span class="workflow-step-index">${index + 1}</span>
                            <div class="workflow-step-content">
                                <div class="workflow-step-meta">
                                    <h3 class="workflow-step-title">${escapeHtml(step.title)}</h3>
                                    <div class="workflow-step-meta-right">
                                        ${durationBadge}
                                        ${currentBadge}
                                        <span class="workflow-step-status workflow-step-status-${escapeHtml(status)}">${statusLabel}</span>
                                        <span class="workflow-step-chevron">${expanded ? "收起" : "展开"}</span>
                                    </div>
                                </div>
                                <p class="workflow-step-summary">${escapeHtml(summary)}</p>
                            </div>
                        </div>
                    </button>
                    <div class="workflow-step-detail" ${expanded ? "" : "hidden"}>${escapeHtml(detail)}</div>
                </article>
            `;
        })
        .join("");

    scrollWorkflowToLatest();
}

function renderWorkflowTraceError(message) {
    if (!workflowTrace) {
        return;
    }
    updateWorkflowStats([], {
        workflowAction: "error",
        knowledgeHits: latestWorkflowMeta.knowledgeHits,
        isStreaming: false,
        currentLabel: "流程失败",
    });
    workflowTrace.innerHTML = `
        <article class="workflow-step workflow-step-error" data-expanded="true">
            <button type="button" class="workflow-step-toggle" aria-expanded="true">
                <div class="workflow-step-header">
                    <span class="workflow-step-index">!</span>
                    <div class="workflow-step-content">
                        <div class="workflow-step-meta">
                            <h3 class="workflow-step-title">流程执行失败</h3>
                            <div class="workflow-step-meta-right">
                                <span class="workflow-step-status workflow-step-status-error">错误</span>
                                <span class="workflow-step-chevron">收起</span>
                            </div>
                        </div>
                        <p class="workflow-step-summary">${escapeHtml(summarizeWorkflowDetail(message))}</p>
                    </div>
                </div>
            </button>
            <div class="workflow-step-detail">${escapeHtml(message)}</div>
        </article>
    `;

    scrollWorkflowToLatest();
}

function renderWorkflowTracePlaceholder(title, summary, detail) {
    if (!workflowTrace) {
        return;
    }
    updateWorkflowStats(activeWorkflowSteps, {
        workflowAction: latestWorkflowMeta.workflowAction,
        knowledgeHits: latestWorkflowMeta.knowledgeHits,
        isStreaming: true,
        currentLabel: title,
    });
    workflowTrace.innerHTML = `
        <article class="workflow-step workflow-step-empty" data-expanded="true">
            <button type="button" class="workflow-step-toggle" aria-expanded="true">
                <div class="workflow-step-header">
                    <span class="workflow-step-index">~</span>
                    <div class="workflow-step-content">
                        <div class="workflow-step-meta">
                            <h3 class="workflow-step-title">${escapeHtml(title)}</h3>
                            <div class="workflow-step-meta-right">
                                <span class="workflow-step-status">等待中</span>
                                <span class="workflow-step-chevron">收起</span>
                            </div>
                        </div>
                        <p class="workflow-step-summary">${escapeHtml(summary)}</p>
                    </div>
                </div>
            </button>
            <div class="workflow-step-detail">${escapeHtml(detail)}</div>
        </article>
    `;

    scrollWorkflowToLatest();
}

function setWorkflowShellCollapsed(collapsed) {
    document.body.classList.toggle("workflow-shell-collapsed", collapsed);
    if (workflowShell) {
        workflowShell.setAttribute("data-collapsed", String(collapsed));
    }
    if (workflowToggleButton) {
        workflowToggleButton.textContent = collapsed ? "展开" : "收起";
        workflowToggleButton.setAttribute("aria-expanded", String(!collapsed));
    }

    try {
        localStorage.setItem(WORKFLOW_SHELL_COLLAPSED_KEY, collapsed ? "1" : "0");
    } catch {
        // Ignore storage access issues.
    }
}

function isMobileWorkflowViewport() {
    return globalThis.matchMedia("(max-width: 920px)").matches;
}

function setWorkflowMobileOpen(open) {
    const nextOpen = isMobileWorkflowViewport() && Boolean(open);
    document.body.classList.toggle("workflow-shell-mobile-open", nextOpen);
    workflowMobileBackdrop?.classList.toggle("hidden", !nextOpen);
    if (workflowShell) {
        workflowShell.setAttribute("aria-hidden", String(isMobileWorkflowViewport() ? !nextOpen : false));
    }
    updateMobileWorkflowTrigger();
    updateWorkflowMobileHandle();
}

function getWorkflowMobileSheetMode() {
    return document.body.classList.contains("workflow-shell-mobile-full") ? "full" : "half";
}

function getStoredWorkflowMobileSheetMode() {
    try {
        return localStorage.getItem(WORKFLOW_MOBILE_MODE_KEY) === "full" ? "full" : "half";
    } catch {
        return "half";
    }
}

function setWorkflowMobileSheetMode(mode) {
    const nextMode = mode === "full" ? "full" : "half";
    document.body.classList.toggle("workflow-shell-mobile-full", nextMode === "full");
    if (workflowShell) {
        workflowShell.setAttribute("data-mobile-mode", nextMode);
    }
    try {
        localStorage.setItem(WORKFLOW_MOBILE_MODE_KEY, nextMode);
    } catch {
        // Ignore storage access issues.
    }
    updateWorkflowMobileHandle();
}

function openWorkflowMobileSheet(mode = getStoredWorkflowMobileSheetMode()) {
    if (!isMobileWorkflowViewport()) {
        return;
    }
    if (sideDrawer && !sideDrawer.classList.contains("hidden")) {
        closeDrawer();
    }
    setWorkflowMobileOpen(true);
    setWorkflowMobileSheetMode(mode);
    scrollWorkflowToLatest();
}

function closeWorkflowMobileSheet() {
    setWorkflowMobileOpen(false);
}

function toggleWorkflowMobileSheet() {
    if (!isMobileWorkflowViewport()) {
        return;
    }
    if (document.body.classList.contains("workflow-shell-mobile-open")) {
        closeWorkflowMobileSheet();
        return;
    }
    openWorkflowMobileSheet();
}

function updateWorkflowMobileHandle() {
    if (!workflowMobileHandle || !workflowMobileHandleText) {
        return;
    }

    const isOpen = document.body.classList.contains("workflow-shell-mobile-open");
    const isFull = getWorkflowMobileSheetMode() === "full";
    workflowMobileHandle.setAttribute("aria-expanded", String(isOpen && isFull));
    workflowMobileHandle.setAttribute("aria-label", isFull ? "收起进度面板高度" : "展开进度面板高度");
    workflowMobileHandleText.textContent = isFull ? "收起一些" : "展开更多";
}

function toggleWorkflowMobileSheetMode() {
    if (!isMobileWorkflowViewport() || !document.body.classList.contains("workflow-shell-mobile-open")) {
        return;
    }
    if (suppressWorkflowMobileHandleClick) {
        suppressWorkflowMobileHandleClick = false;
        return;
    }
    setWorkflowMobileSheetMode(getWorkflowMobileSheetMode() === "full" ? "half" : "full");
}

function handleWorkflowMobileHandlePointerDown(event) {
    if (!isMobileWorkflowViewport() || !document.body.classList.contains("workflow-shell-mobile-open")) {
        return;
    }
    workflowMobileHandlePointerId = event.pointerId;
    workflowMobileHandleStartY = event.clientY;
    suppressWorkflowMobileHandleClick = false;
    workflowMobileHandle?.setPointerCapture?.(event.pointerId);
}

function handleWorkflowMobileHandlePointerMove(event) {
    if (workflowMobileHandlePointerId !== event.pointerId) {
        return;
    }
    if (Math.abs(event.clientY - workflowMobileHandleStartY) > 18) {
        suppressWorkflowMobileHandleClick = true;
    }
}

function handleWorkflowMobileHandlePointerUp(event) {
    if (workflowMobileHandlePointerId !== event.pointerId) {
        return;
    }

    const deltaY = event.clientY - workflowMobileHandleStartY;
    workflowMobileHandle?.releasePointerCapture?.(event.pointerId);
    resetWorkflowMobileHandlePointer();

    if (deltaY <= -48) {
        setWorkflowMobileSheetMode("full");
        return;
    }

    if (deltaY >= 72) {
        if (getWorkflowMobileSheetMode() === "full") {
            setWorkflowMobileSheetMode("half");
        } else {
            closeWorkflowMobileSheet();
        }
    }
}

function resetWorkflowMobileHandlePointer() {
    workflowMobileHandlePointerId = null;
    workflowMobileHandleStartY = 0;
}

function updateMobileWorkflowTrigger(meta = latestWorkflowMeta, steps = activeWorkflowSteps) {
    if (!mobileWorkflowTrigger) {
        return;
    }

    const isOpen = document.body.classList.contains("workflow-shell-mobile-open");
    const currentLabel = formatWorkflowActionLabel(meta, steps);
    mobileWorkflowTrigger.textContent = meta.isStreaming ? `处理中：${currentLabel}` : steps.length ? "查看处理进度" : "打开处理进度";
    mobileWorkflowTrigger.setAttribute("aria-expanded", String(isOpen));
}

function toggleWorkflowShell() {
    const collapsed = document.body.classList.contains("workflow-shell-collapsed");
    setWorkflowShellCollapsed(!collapsed);
}

function syncWorkflowViewportState() {
    if (isMobileWorkflowViewport()) {
        setWorkflowShellCollapsed(false);
        if (!document.body.classList.contains("workflow-shell-mobile-open")) {
            setWorkflowMobileSheetMode(getStoredWorkflowMobileSheetMode());
        }
        if (workflowShell) {
            workflowShell.setAttribute(
                "aria-hidden",
                String(!document.body.classList.contains("workflow-shell-mobile-open"))
            );
        }
        updateMobileWorkflowTrigger();
        return;
    }

    document.body.classList.remove("workflow-shell-mobile-open");
    document.body.classList.remove("workflow-shell-mobile-full");
    workflowMobileBackdrop?.classList.add("hidden");
    if (workflowShell) {
        workflowShell.setAttribute("aria-hidden", "false");
    }
    updateMobileWorkflowTrigger();
    updateWorkflowMobileHandle();
}

function restoreWorkflowShellState() {
    if (!workflowShell || !workflowToggleButton) {
        return;
    }

    if (globalThis.matchMedia("(max-width: 920px)").matches) {
        setWorkflowShellCollapsed(false);
        return;
    }

    try {
        setWorkflowShellCollapsed(localStorage.getItem(WORKFLOW_SHELL_COLLAPSED_KEY) === "1");
    } catch {
        setWorkflowShellCollapsed(false);
    }
}

function scrollWorkflowToLatest() {
    if (!workflowTraceWrap || document.body.classList.contains("workflow-shell-collapsed")) {
        return;
    }
    workflowTraceWrap.scrollTop = workflowTraceWrap.scrollHeight;
}

async function openWorkflowTraceStream(requestId) {
    stopWorkflowTraceStream();
    activeWorkflowRequestId = requestId;
    activeWorkflowSteps = [];

    if (typeof EventSource !== "function") {
        renderWorkflowTracePlaceholder(
            "状态更新不可用",
            "当前浏览器不支持实时状态连接。",
            "这次请求会在完成后展示最终状态记录。"
        );
        return false;
    }

    let hasReceivedEvent = false;
    renderWorkflowTracePlaceholder(
        "正在连接状态更新",
        "正在等待状态消息。",
        "连接建立后，这里会逐步显示当前请求的处理进度。"
    );

    const apiOrigin = await resolveApiOrigin();
    const streamUrl = buildApiUrl(`/chat/workflow-events?request_id=${encodeURIComponent(requestId)}`, apiOrigin);
    const source = new EventSource(streamUrl, { withCredentials: true });
    activeWorkflowStream = source;

    globalThis.setTimeout(() => {
        if (!hasReceivedEvent && activeWorkflowStream === source) {
            renderWorkflowTracePlaceholder(
                "状态更新稍慢",
                "请求已经发出，请稍候。",
                "如果收到新的状态消息，这里会自动更新。"
            );
        }
    }, 4000);

    source.onopen = () => {
        if (activeWorkflowStream !== source) {
            return;
        }
        renderWorkflowTracePlaceholder(
            "状态连接已建立",
            "正在等待第一条状态消息。",
            "这里会随着处理进度逐条更新。"
        );
    };

    source.onmessage = (event) => {
        let payload;
        try {
            payload = JSON.parse(event.data);
        } catch {
            return;
        }
        hasReceivedEvent = true;
        handleWorkflowStreamEvent(payload);
    };

    source.onerror = () => {
        if (activeWorkflowStream === source && !hasReceivedEvent) {
            renderWorkflowTracePlaceholder(
                "状态连接失败",
                "无法建立实时状态连接。",
                "这次请求会在完成后展示最终状态记录。"
            );
        }
    };

    return true;
}

function stopWorkflowTraceStream() {
    if (activeWorkflowStream) {
        activeWorkflowStream.close();
        activeWorkflowStream = null;
    }
    activeWorkflowRequestId = null;
    latestWorkflowMeta = { ...latestWorkflowMeta, isStreaming: false, currentLabel: undefined };
    updateMobileWorkflowTrigger();
}

function handleWorkflowStreamEvent(payload) {
    if (!payload || typeof payload !== "object") {
        return;
    }

    if (payload.type === "trace-step" && payload.step) {
        activeWorkflowSteps = [...activeWorkflowSteps, payload.step];
        renderWorkflowTrace(activeWorkflowSteps, {
            workflowAction: latestWorkflowMeta.workflowAction,
            knowledgeHits: latestWorkflowMeta.knowledgeHits,
            isStreaming: true,
            currentLabel: payload.step.title,
        });
        return;
    }

    if (payload.type === "error") {
        stopWorkflowTraceStream();
        renderWorkflowTraceError(payload.message || "处理失败。请稍后重试。");
        return;
    }

    if (payload.type === "complete") {
        stopWorkflowTraceStream();
    }
}

function handleWorkflowTraceToggle(event) {
    const toggle = event.target.closest(".workflow-step-toggle");
    if (!toggle || !workflowTrace || !workflowTrace.contains(toggle)) {
        return;
    }

    const step = toggle.closest(".workflow-step");
    const detail = step?.querySelector(".workflow-step-detail");
    const chevron = toggle.querySelector(".workflow-step-chevron");
    if (!step || !detail) {
        return;
    }

    const expanded = toggle.getAttribute("aria-expanded") === "true";
    const nextExpanded = !expanded;
    toggle.setAttribute("aria-expanded", String(nextExpanded));
    step.dataset.expanded = String(nextExpanded);
    detail.hidden = !nextExpanded;
    if (chevron) {
        chevron.textContent = nextExpanded ? "收起" : "展开";
    }
}

function handleMessageSectionToggle(event) {
    const toggle = event.target.closest(".message-section-toggle");
    if (!toggle || !chatStream || !chatStream.contains(toggle)) {
        return;
    }

    const section = toggle.closest(".message-section");
    const content = section?.querySelector(".message-section-content");
    const chevron = toggle.querySelector(".message-section-chevron");
    if (!section || !content) {
        return;
    }

    const expanded = toggle.getAttribute("aria-expanded") === "true";
    const nextExpanded = !expanded;
    toggle.setAttribute("aria-expanded", String(nextExpanded));
    section.dataset.expanded = String(nextExpanded);
    content.hidden = !nextExpanded;
    if (chevron) {
        chevron.textContent = nextExpanded ? "收起" : "查看";
    }
}

function workflowStatusLabel(status) {
    switch (status) {
        case "active":
            return "进行中";
        case "pending":
            return "待执行";
        case "skipped":
            return "跳过";
        case "error":
            return "错误";
        default:
            return "完成";
    }
}

function summarizeWorkflowDetail(detail) {
    const normalized = String(detail).replace(/\s+/g, " ").trim();
    if (normalized.length <= 30) {
        return normalized;
    }
    return `${normalized.slice(0, 30)}...`;
}

function formatWorkflowDuration(durationMs) {
    if (durationMs < 1000) {
        return `${durationMs} ms`;
    }
    return `${(durationMs / 1000).toFixed(1)} s`;
}

function updateWorkflowStats(steps, meta = {}) {
    if (!workflowTotalDuration || !workflowCurrentAction || !workflowKnowledgeCount) {
        return;
    }

    const totalDurationMs = steps.reduce(
        (sum, step) => sum + (typeof step.duration_ms === "number" ? step.duration_ms : 0),
        0
    );
    workflowTotalDuration.textContent = steps.length ? formatWorkflowDuration(totalDurationMs) : "--";
    workflowCurrentAction.textContent = formatWorkflowActionLabel(meta, steps);
    workflowKnowledgeCount.textContent =
        typeof meta.knowledgeHits === "number" ? `${meta.knowledgeHits} 条` : steps.length ? "0 条" : "--";
    updateMobileWorkflowTrigger(meta, steps);
}

function formatWorkflowActionLabel(meta, steps) {
    if (meta.currentLabel) {
        return meta.currentLabel;
    }
    if (meta.isStreaming && steps.length) {
        return steps[steps.length - 1].title;
    }

    switch (meta.workflowAction) {
        case "book_meeting":
            return "已提交预约申请";
        case "collect_booking_details":
            return "补充预约信息";
        case "advise_only":
            return "仅提供建议";
        case "review_queue":
            return "进入待审核队列";
        case "human_handoff":
            return "已转人工处理";
        case "answer":
            return "整理回复";
        case "error":
            return "处理失败";
        default:
            return steps.length ? steps[steps.length - 1].title : "等待消息";
    }
}

function applyBranding(ownerName, ownerRole, homepageUrl) {
    assistantLabel = formatAssistantLabel(ownerName);
    document.title = assistantLabel;
    if (assistantName) {
        assistantName.textContent = assistantLabel;
    }
    if (topbarTitle) {
        topbarTitle.textContent = formatWorkspaceTitle(ownerName);
    }
    if (topbarSubtitle) {
        topbarSubtitle.textContent = formatWorkspaceSubtitle(ownerName, ownerRole);
    }
    if (homepageLink) {
        const normalizedHomepageUrl = homepageUrl ? String(homepageUrl).trim() : "";
        homepageLink.hidden = !normalizedHomepageUrl;
        homepageLink.href = normalizedHomepageUrl || "#";
    }
    if (chatQuestion) {
        chatQuestion.placeholder = "直接说问题；如果想约时间，请把 agenda、blocker 和 draft 也写上。";
    }
}

function formatAssistantLabel(ownerName) {
    const normalizedOwnerName = ownerName ? String(ownerName).trim() : "";
    if (!normalizedOwnerName) {
        return "我的学术分身";
    }
    return /[A-Za-z]/.test(normalizedOwnerName)
        ? `${normalizedOwnerName} 的分身`
        : `${normalizedOwnerName}的分身`;
}

function formatWorkspaceTitle(ownerName) {
    const normalizedOwnerName = ownerName ? String(ownerName).trim() : "";
    if (!normalizedOwnerName) {
        return "我的分身办公室";
    }
    return /[A-Za-z]/.test(normalizedOwnerName)
        ? `${normalizedOwnerName} 的分身办公室`
        : `${normalizedOwnerName}的分身办公室`;
}

function formatWorkspaceSubtitle(ownerName, ownerRole) {
    const normalizedOwnerName = ownerName ? String(ownerName).trim() : "";
    const normalizedOwnerRole = ownerRole ? String(ownerRole).trim() : "";
    if (!normalizedOwnerName) {
        return "这不是通用模板，而是围绕你自己的课程、研究和预约流程整理的线上前台。";
    }
    if (normalizedOwnerRole) {
        return `围绕${normalizedOwnerName}这位${normalizedOwnerRole}的课程、研究和预约节奏整理的线上前台。`;
    }
    return `围绕${normalizedOwnerName}本人的课程、研究和预约节奏整理的线上前台。`;
}

function shouldPromptProfileSetup() {
    if (!studentNameInput || !studentEmailInput) {
        return false;
    }
    return studentNameInput.value.trim().toLowerCase() === "guest" && !studentEmailInput.value.trim();
}

function maybePromptProfileSetup() {
    if (!shouldPromptProfileSetup()) {
        return;
    }

    try {
        if (sessionStorage.getItem(PROFILE_PROMPT_KEY) === "1") {
            return;
        }
        sessionStorage.setItem(PROFILE_PROMPT_KEY, "1");
    } catch {
        // Ignore storage access issues and still show the prompt once for this load.
    }

    openDrawer();
    studentNameInput.focus();
    studentNameInput.select();
}

function openModal(element) {
    closeWorkflowMobileSheet();
    modalOverlay.classList.remove("hidden");
    element.classList.remove("hidden");
    element.setAttribute("aria-hidden", "false");
    syncFloatingWorkflowTriggerState();
}

function closeModals() {
    modalOverlay.classList.add("hidden");
    [knowledgeModal, bookingModal, adminLoginModal, userRegisterModal, userLoginModal, availabilityModal, bookingAdminModal, escalationAdminModal, memoryProfilesModal, questionAnalyticsModal].forEach((element) => {
        element.classList.add("hidden");
        element.setAttribute("aria-hidden", "true");
    });
    closeDrawer();
    syncFloatingWorkflowTriggerState();
}

function openDrawer() {
    closeWorkflowMobileSheet();
    modalOverlay.classList.remove("hidden");
    sideDrawer.classList.remove("hidden");
    sideDrawer.setAttribute("aria-hidden", "false");
    syncFloatingWorkflowTriggerState();
}

function closeDrawer() {
    sideDrawer.classList.add("hidden");
    sideDrawer.setAttribute("aria-hidden", "true");
    if (
        knowledgeModal.classList.contains("hidden") &&
        bookingModal.classList.contains("hidden") &&
        adminLoginModal.classList.contains("hidden") &&
        userRegisterModal.classList.contains("hidden") &&
        userLoginModal.classList.contains("hidden") &&
        availabilityModal.classList.contains("hidden") &&
        bookingAdminModal.classList.contains("hidden") &&
        escalationAdminModal.classList.contains("hidden") &&
        memoryProfilesModal.classList.contains("hidden") &&
        questionAnalyticsModal.classList.contains("hidden")
    ) {
        modalOverlay.classList.add("hidden");
    }
    syncFloatingWorkflowTriggerState();
}

function syncFloatingWorkflowTriggerState() {
    const hasOverlaySurface = !sideDrawer.classList.contains("hidden") || !modalOverlay.classList.contains("hidden");
    document.body.classList.toggle("workflow-trigger-suppressed", hasOverlaySurface);
}

async function handleAdminLogout() {
    try {
        await apiRequest("/auth/admin/logout", { method: "POST" });
        bookingList.innerHTML = "";
        escalationList.innerHTML = "";
        memoryProfilesSummary.innerHTML = "";
        memoryProfilesList.innerHTML = "";
        questionAnalyticsSummary.innerHTML = "";
        questionAnalyticsClusters.innerHTML = "";
        questionAnalyticsGaps.innerHTML = "";
        questionAnalyticsUnresolved.innerHTML = "";
        questionAnalyticsHandoffs.innerHTML = "";
        questionAnalyticsDrafts.innerHTML = "";
        resetManagedServicePanel();
        setInlineStatus(escalationAdminResponse, "这里放必须由你亲自接手的请求。", "empty");
        setInlineStatus(memoryProfilesResponse, "需要查学生长期记录时再打开这里。", "empty");
        setInlineStatus(questionAnalyticsResponse, "这里汇总近期问题和缺口，适合按周回看。", "empty");
        await refreshSession();
        closeDrawer();
    } catch (error) {
        setInlineStatus(adminLoginResponse, error.message, "error");
    }
}

async function handleUserLogout() {
    try {
        await apiRequest("/auth/user/logout", { method: "POST" });
        await refreshUserSession();
        closeDrawer();
    } catch (error) {
        setInlineStatus(userLoginResponse, error.message, "error");
    }
}

function autoResizeTextarea() {
    const textarea = document.getElementById("chat-question");
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
}

function toIso(value) {
    return value ? new Date(value).toISOString() : null;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function seedBookingDefaults() {
    const now = new Date();
    now.setMinutes(0, 0, 0);
    now.setHours(Math.max(10, now.getHours() + 1));
    const end = new Date(now.getTime() + 30 * 60 * 1000);
    document.getElementById("booking-start").value = toLocalInputValue(now);
    document.getElementById("booking-end").value = toLocalInputValue(end);
}

function createConversationId() {
    if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
        return globalThis.crypto.randomUUID();
    }
    return `conv-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function toLocalInputValue(date) {
    const pad = (value) => String(value).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function normalizeAvailabilityState(schedule) {
    const weekOf = schedule.week_of || getStartOfWeekIso(new Date());
    const selectedSlots = new Set();
    const dayNotes = new Map();

    (schedule.days || []).forEach((day) => {
        if (day.note) {
            dayNotes.set(day.date, day.note);
        }
        (day.windows || []).forEach((window) => {
            expandWindowToSlots(day.date, window.start, window.end).forEach((slot) => {
                selectedSlots.add(`${day.date}|${slot}`);
            });
        });
    });

    return {
        weekOf,
        timezone: schedule.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai",
        selectedSlots,
        dayNotes,
    };
}

function buildAvailabilityPayload(state) {
    const days = getWeekDates(state.weekOf).map((day) => {
        const slots = [...state.selectedSlots]
            .filter((key) => key.startsWith(`${day.iso}|`))
            .map((key) => key.split("|")[1])
            .sort();
        const windows = compressSlotsToWindows(slots);
        const note = state.dayNotes.get(day.iso) || null;
        return {
            date: day.iso,
            windows,
            note,
        };
    });

    return {
        week_of: state.weekOf,
        timezone: state.timezone,
        days: days.filter((day) => day.windows.length || day.note),
    };
}

function buildAvailabilitySlots() {
    const slots = [];
    for (let hour = AVAILABILITY_START_HOUR; hour < AVAILABILITY_END_HOUR; hour += 1) {
        slots.push(`${String(hour).padStart(2, "0")}:00`);
        slots.push(`${String(hour).padStart(2, "0")}:30`);
    }
    return slots;
}

function buildSlotsForWindow(start, end) {
    return expandWindowToSlots("", start, end);
}

function expandWindowToSlots(dateIso, start, end) {
    const slots = [];
    let cursor = clockTextToMinutes(start);
    const endMinutes = clockTextToMinutes(end);
    while (cursor < endMinutes) {
        slots.push(minutesToClockText(cursor));
        cursor += AVAILABILITY_SLOT_MINUTES;
    }
    return slots;
}

function compressSlotsToWindows(slots) {
    if (!slots.length) {
        return [];
    }

    const minutes = slots.map(clockTextToMinutes).sort((left, right) => left - right);
    const windows = [];
    let startMinutes = minutes[0];
    let previousMinutes = minutes[0];

    for (let index = 1; index < minutes.length; index += 1) {
        const currentMinutes = minutes[index];
        if (currentMinutes !== previousMinutes + AVAILABILITY_SLOT_MINUTES) {
            windows.push({
                start: minutesToClockText(startMinutes),
                end: minutesToClockText(previousMinutes + AVAILABILITY_SLOT_MINUTES),
            });
            startMinutes = currentMinutes;
        }
        previousMinutes = currentMinutes;
    }

    windows.push({
        start: minutesToClockText(startMinutes),
        end: minutesToClockText(previousMinutes + AVAILABILITY_SLOT_MINUTES),
    });
    return windows;
}

function clockTextToMinutes(clockText) {
    const [hourText, minuteText] = String(clockText).split(":");
    return Number(hourText) * 60 + Number(minuteText);
}

function minutesToClockText(totalMinutes) {
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

function getWeekDates(weekOfIso) {
    const start = new Date(`${weekOfIso}T00:00:00`);
    return Array.from({ length: AVAILABILITY_DAY_COUNT }, (_, offset) => {
        const date = new Date(start);
        date.setDate(start.getDate() + offset);
        return {
            iso: formatDateIso(date),
            label: formatWeekdayLabel(date),
        };
    });
}

function getStartOfWeekIso(date) {
    const normalized = new Date(date);
    normalized.setHours(0, 0, 0, 0);
    const day = normalized.getDay();
    const diff = day === 0 ? -6 : 1 - day;
    normalized.setDate(normalized.getDate() + diff);
    return formatDateIso(normalized);
}

function formatDateIso(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function formatWeekdayLabel(date) {
    return date.toLocaleDateString("zh-CN", {
        weekday: "short",
        month: "numeric",
        day: "numeric",
    });
}

function formatBookingWindow(startAt, endAt) {
    const start = new Date(startAt);
    const end = new Date(endAt);
    return `${formatDateIso(start)} ${String(start.getHours()).padStart(2, "0")}:${String(start.getMinutes()).padStart(2, "0")} → ${String(end.getHours()).padStart(2, "0")}:${String(end.getMinutes()).padStart(2, "0")}`;
}

function formatDateTime(value) {
    if (!value) {
        return "未知";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return String(value);
    }
    return date.toLocaleString("zh-CN", {
        hour12: false,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function formatFollowUpActionLabel(actionType) {
    switch (actionType) {
        case "recommended_reading":
            return "推荐阅读";
        case "todo_review":
            return "待办回顾";
        case "office_hour_recommendation":
            return "Office Hour";
        case "course_resource_recommendation":
            return "课程资源";
        case "post_meeting_summary":
            return "会后总结邮件";
        default:
            return "后续动作";
    }
}

function formatPercentage(value) {
    return `${Math.round(Number(value || 0) * 100)}%`;
}

function formatProfileCategoryLabel(category) {
    const labels = {
        identity: "身份信息",
        course_context: "场景背景",
        recent_topic: "近期话题",
        booking_preference: "预约偏好",
        collaboration_preference: "协作偏好",
    };
    return labels[category] || category;
}

seedBookingDefaults();
autoResizeTextarea();
restoreWorkflowShellState();
syncWorkflowViewportState();

async function initializePage() {
    await refreshStatus();
    await refreshSession();
    await refreshUserSession();
    maybePromptProfileSetup();
}

initializePage();