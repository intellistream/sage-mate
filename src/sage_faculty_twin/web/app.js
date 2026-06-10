const statusPill = document.getElementById("status-pill");
const modelPill = document.getElementById("model-pill");
const knowledgePill = document.getElementById("knowledge-pill");
const modePill = document.getElementById("mode-pill");
const onlineOverviewGrid = document.getElementById("online-overview-grid");
const onlineBenchmarkTable = document.getElementById("online-benchmark-table");
const onlineOverviewCopy = document.getElementById("online-overview-copy");
const topbarServiceStatus = document.getElementById("topbar-service-status");
const topbarUserCount = document.getElementById("topbar-user-count");
const topbarQuestionCount = document.getElementById("topbar-question-count");
const topbarModelStatus = document.getElementById("topbar-model-status");
const topbarMobileHistoryToggleButton = document.getElementById("topbar-mobile-history-toggle");
const topbarActionsToggleButton = document.getElementById("topbar-actions-toggle");
const topbarActions = document.querySelector(".topbar-actions");
const topbarShell = document.querySelector(".topbar");
const topbarStatusSummary = document.getElementById("topbar-status-summary");
const historyList = document.getElementById("history-list");
const historyRailToggleButton = document.getElementById("history-rail-toggle");
const historyNewChatButton = document.getElementById("history-new-chat");
const chatStream = document.getElementById("chat-stream");
const modalOverlay = document.getElementById("modal-overlay");
const settingsDrawer = document.getElementById("settings-drawer");
const statusDrawer = document.getElementById("status-drawer");
const identityModal = document.getElementById("identity-modal");
const knowledgeModal = document.getElementById("knowledge-modal");
const bookingModal = document.getElementById("booking-modal");
const suggestionModal = document.getElementById("suggestion-modal");
const availabilityModal = document.getElementById("availability-modal");
const bookingAdminModal = document.getElementById("booking-admin-modal");
const escalationAdminModal = document.getElementById("escalation-admin-modal");
const memoryProfilesModal = document.getElementById("memory-profiles-modal");
const operationsConsoleModal = document.getElementById("operations-console-modal");
const questionAnalyticsModal = document.getElementById("question-analytics-modal");
const adminLoginModal = document.getElementById("admin-login-modal");
const userRegisterModal = document.getElementById("user-register-modal");
const userLoginModal = document.getElementById("user-login-modal");
const adminLoginResponse = document.getElementById("admin-login-response");
const userRegisterResponse = document.getElementById("user-register-response");
const userLoginResponse = document.getElementById("user-login-response");
const userRegisterProfileInput = document.getElementById("user-register-profile");
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
const topbarUserBadge = document.getElementById("topbar-user-badge");
const topbarUserBadgeName = document.getElementById("topbar-user-badge-name");
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
const openSuggestionsButton = document.getElementById("open-suggestions");
const topbarHistoryToggleButton = document.getElementById("topbar-history-toggle");
const topbarNewChatButton = document.getElementById("topbar-new-chat");
const openBookingListButton = document.getElementById("open-booking-list");
const openEscalationQueueButton = document.getElementById("open-escalation-queue");
const openMemoryProfilesButton = document.getElementById("open-memory-profiles");
const openOperationsConsoleButton = document.getElementById("open-operations-console");
const openQuestionAnalyticsButton = document.getElementById("open-question-analytics");
const openAvailabilityEditorButton = document.getElementById("open-availability-editor");
const assistantName = document.getElementById("assistant-name");
const topbarTitle = document.getElementById("topbar-title");
const topbarSubtitle = document.getElementById("topbar-subtitle");
const homepageLink = document.getElementById("homepage-link");
const chatQuestion = document.getElementById("chat-question");
const chatFileInput = document.getElementById("chat-file-input");
const composerUploadButton = document.getElementById("composer-upload-button");
const composerAttachmentList = document.getElementById("composer-attachment-list");
const composerUploadHint = document.getElementById("composer-upload-hint");
const courseContextInput = document.getElementById("course-context");
const visitorProfileInput = document.getElementById("visitor-profile");
const studentNameInput = document.getElementById("student-name");
const studentEmailInput = document.getElementById("student-email");
const profileDrawerCopy = document.getElementById("profile-drawer-copy");
const bookingStudentNameInput = document.getElementById("booking-student-name");
const bookingEmailInput = document.getElementById("booking-email");
const composerProfileChip = document.getElementById("composer-profile-chip");
const composerContextChip = document.getElementById("composer-context-chip");
const composerWorkflowChip = document.getElementById("composer-workflow-chip");
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
const workflowPlanCard = document.getElementById("workflow-plan-card");
const workflowPlanHeading = document.getElementById("workflow-plan-heading");
const workflowPlanBadge = document.getElementById("workflow-plan-badge");
const workflowPlanCopy = document.getElementById("workflow-plan-copy");
const workflowPlanNote = document.getElementById("workflow-plan-note");
const workflowPlanDetails = document.getElementById("workflow-plan-details");
const workflowPlanToggle = document.getElementById("workflow-plan-toggle");
const workflowPlanSteps = document.getElementById("workflow-plan-steps");
const workflowShadowPlanPanel = document.getElementById("workflow-shadow-plan-panel");
const workflowShadowPlanHeading = document.getElementById("workflow-shadow-plan-heading");
const workflowShadowPlanBadge = document.getElementById("workflow-shadow-plan-badge");
const workflowShadowPlanCopy = document.getElementById("workflow-shadow-plan-copy");
const workflowShadowPlanDetails = document.getElementById("workflow-shadow-plan-details");
const workflowShadowPlanToggle = document.getElementById("workflow-shadow-plan-toggle");
const workflowShadowPlanSteps = document.getElementById("workflow-shadow-plan-steps");
const workflowPlanComparePanel = document.getElementById("workflow-plan-compare-panel");
const workflowPlanCompareHeading = document.getElementById("workflow-plan-compare-heading");
const workflowPlanCompareBadge = document.getElementById("workflow-plan-compare-badge");
const workflowPlanCompareCopy = document.getElementById("workflow-plan-compare-copy");
const workflowPlanCompareDetails = document.getElementById("workflow-plan-compare-details");
const workflowPlanCompareToggle = document.getElementById("workflow-plan-compare-toggle");
const workflowPlanCompareSteps = document.getElementById("workflow-plan-compare-steps");
const mobileWorkflowTrigger = document.getElementById("mobile-workflow-trigger");
const workflowMobileBackdrop = document.getElementById("workflow-mobile-backdrop");
const initialChatStreamMarkup = chatStream?.innerHTML || "";

const chatForm = document.getElementById("chat-form");
const deepThinkingCheckbox = document.getElementById("deep-thinking-checkbox");
const adminLoginForm = document.getElementById("admin-login-form");
const userRegisterForm = document.getElementById("user-register-form");
const userLoginForm = document.getElementById("user-login-form");
const knowledgeForm = document.getElementById("knowledge-form");
const bookingForm = document.getElementById("booking-form");
const suggestionForm = document.getElementById("suggestion-form");
const chatSubmitButton = chatForm.querySelector('button[type="submit"]');
let deepThinkingExplicitlyEnabled = Boolean(deepThinkingCheckbox?.checked);

deepThinkingCheckbox?.addEventListener("change", () => {
    deepThinkingExplicitlyEnabled = Boolean(deepThinkingCheckbox.checked);
});

const knowledgeResponse = document.getElementById("knowledge-response");
const bookingResponse = document.getElementById("booking-response");
const suggestionResponse = document.getElementById("suggestion-response");
const knowledgeList = document.getElementById("knowledge-list");
const suggestionList = document.getElementById("suggestion-list");
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
const operationsWindow = document.getElementById("operations-window");
const operationsResponse = document.getElementById("operations-response");
const operationsSummary = document.getElementById("operations-summary");
const operationsQueues = document.getElementById("operations-queues");
const operationsWorkflowReplaySummary = document.getElementById("operations-workflow-replay-summary");
const operationsWorkflowReplayList = document.getElementById("operations-workflow-replay-list");
const operationsTasks = document.getElementById("operations-tasks");
const operationsBookings = document.getElementById("operations-bookings");
const operationsStudentProfiles = document.getElementById("operations-student-profiles");
const operationsSatisfaction = document.getElementById("operations-satisfaction");
const operationsGaps = document.getElementById("operations-gaps");
const operationsArtifactDrafts = document.getElementById("operations-artifact-drafts");
const operationsEscalations = document.getElementById("operations-escalations");
const operationsFollowUps = document.getElementById("operations-follow-ups");
const operationsSuggestions = document.getElementById("operations-suggestions");
const AVAILABILITY_SLOT_MINUTES = 30;
const AVAILABILITY_START_HOUR = 9;
const AVAILABILITY_END_HOUR = 18;
const AVAILABILITY_DAY_COUNT = 7;
const WORKFLOW_SHELL_COLLAPSED_KEY = "myTwinWorkflowShellCollapsed";
const WORKFLOW_MOBILE_MODE_KEY = "myTwinWorkflowMobileMode";
const VISITOR_IDENTITY_SELECTED_KEY = "myTwinVisitorIdentitySelected";
const VISITOR_PROFILE_STORAGE_KEY = "myTwinVisitorProfile";
const CHAT_HISTORY_STORAGE_KEY = "myTwinConversationHistory";
const CHAT_HISTORY_META_STORAGE_KEY = "myTwinConversationHistoryMeta";
const HISTORY_RAIL_COLLAPSED_KEY = "myTwinHistoryRailCollapsed";
const ONLINE_PRESENCE_CLIENT_KEY = "myTwinOnlinePresenceClientId";
const ONLINE_PRESENCE_INTERVAL_MS = 30_000;
const STATUS_REFRESH_INTERVAL_MS = 30_000;
const HEALTH_REQUEST_TIMEOUT_MS = 20_000;
const HEALTH_REQUEST_RETRY_COUNT = 1;
const HEALTH_SNAPSHOT_STALE_MS = 3 * 60_000;
const MAX_CHAT_HISTORY_ITEMS = 18;
const DEFAULT_CONVERSATION_TITLE = "新对话";
const LOCAL_API_PORT_CANDIDATES = ["55601", "8010", "8000"];
const MAX_WORKFLOW_STEP_TITLE_LENGTH = 10;
const MAX_CHAT_UPLOAD_FILES = 4;
const MAX_CHAT_UPLOAD_BYTES = 5 * 1024 * 1024;
const DEFAULT_COMPOSER_UPLOAD_HINT = "支持 PDF、TXT、MD、CSV、JSON、PY、YAML、LOG，最多 4 个文件。";
const SUPPORTED_CHAT_UPLOAD_SUFFIXES = new Set([".pdf", ".txt", ".md", ".csv", ".json", ".py", ".yaml", ".yml", ".log"]);
const WORKFLOW_PHASE_DEFINITIONS = [
    { key: "intake", label: "接入", icon: "inbox" },
    { key: "decide", label: "判断", icon: "branch" },
    { key: "retrieve", label: "检索", icon: "search" },
    { key: "answer", label: "回答", icon: "message" },
    { key: "finalize", label: "收尾", icon: "checklist" },
    { key: "return", label: "返回", icon: "send" },
];
const WORKFLOW_STEP_SHORT_LABELS = {
    bootstrap: "接收问题",
    workflow_plan_preview: "预览路径",
    interaction_understand: "判断意图",
    booking_prepare: "补齐预约",
    booking_execute: "提交预约",
    knowledge_write: "写入知识",
    knowledge_retrieve: "查资料",
    memory_retrieve: "找上下文",
    prompt_build: "整理上下文",
    llm_answer: "生成回复",
    follow_up_plan: "整理后续",
    memory_usefulness_score: "检查证据",
    memory_persist: "写入记忆",
    artifact_memory_writeback: "记录材料",
    memory_profile_consolidate: "更新画像",
    response_render: "返回结果",
    current_stage: "当前处理中",
};
let assistantLabel = "我的学术分身";
let activeConversationId = createConversationId();
let activeWorkflowStream = null;
let activeWorkflowRequestId = null;
let lastAutoChatQuestion = chatQuestion?.value?.trim() || "";
let lastAutoCourseContext = courseContextInput?.value?.trim() || "";
let activeWorkflowSteps = [];
let availabilityEditorState = null;
let workflowMobileHandlePointerId = null;
let workflowMobileHandleStartY = 0;
let suppressWorkflowMobileHandleClick = false;
let latestWorkflowMeta = {
    workflowAction: null,
    knowledgeHits: null,
    isStreaming: false,
    plannerPreview: null,
    shadowPlannerPreview: null,
    plannerComparison: null,
};
let workflowPlanDecayTimer = null;
let workflowPlanLastSignature = "";
let latestManagedServiceEvent = null;
let isAdminSession = false;
let isUserAuthenticated = false;
let currentUserAccountEmail = "";
let pendingChatAttachments = [];
let conversationHistoryScope = resolveConversationHistoryStorageScope();
let conversationHistoryEntries = loadConversationHistory(conversationHistoryScope);
let serverConversationEntries = [];
let conversationHistoryMeta = loadConversationHistoryMeta(conversationHistoryScope);
let currentConversationTitle = DEFAULT_CONVERSATION_TITLE;
let currentConversationPreview = "";
let onlinePresenceHeartbeatTimer = null;
let statusRefreshTimer = null;
let lastHealthyStatusSnapshot = null;
let lastHealthyStatusAt = 0;
let resolvedApiOrigin = typeof globalThis.__SAGE_FACULTY_TWIN_API_ORIGIN__ === "string"
    ? globalThis.__SAGE_FACULTY_TWIN_API_ORIGIN__.trim()
    : "";
let apiOriginResolutionPromise = null;
const VISITOR_PROFILE_CONFIGS = {
    general_visitor: {
        label: "一般访客",
        defaultContext: "初次来访",
        defaultQuestion: "张老师主要研究什么方向？",
        placeholder: "先问研究、资料或预约。",
        drawerHint: "优先参考主页、研究和预约资料。",
        introLines: [
            "研究、资料、预约，都可以直接问。",
            "预约请带 agenda 和当前问题。",
        ],
        quickActions: [
            { label: "先了解研究方向", question: "张老师主要研究什么方向？", context: "初次来访" },
            { label: "问预约准备", question: "如果想预约一次讨论，我需要先准备什么？", context: "初次来访" },
            { label: "找公开资料", question: "有没有适合先看的公开资料？", context: "初次来访" },
        ],
    },
    hust_undergraduate: {
        label: "华科本科生",
        defaultContext: "大模型推理引擎课程答疑",
        defaultQuestion: "大模型推理引擎 Tutorial 7 主要讲了什么，我应该先看哪部分？",
        placeholder: "写清课程名、讲次、实验编号或卡点。",
        drawerHint: "优先参考大模型推理引擎、数据库实验课和答疑资料。",
        introLines: [
            "大模型推理引擎、数据库实验课、office hour，直接问。",
            "带上课程名、编号和卡点会更准。",
        ],
        quickActions: [
            { label: "问推理引擎 Tutorial", question: "大模型推理引擎 Tutorial 7 主要讲了什么，我应该先看哪部分？", context: "大模型推理引擎课程答疑" },
            { label: "问数据库实验", question: "数据库实验课开始前，我应该先准备哪些环境和材料？", context: "数据库实验课答疑" },
            { label: "约 office hour", question: "如果我想约 office hour 讨论课程或实验问题，需要先带哪些材料？", context: "本科课程答疑" },
        ],
    },
    paper_writing_student: {
        label: "论文写作课同学",
        defaultContext: "论文写作课",
        defaultQuestion: "论文写作课第 7 讲主要讲什么？",
        placeholder: "写清讲次、阶段和 blocker。",
        drawerHint: "优先参考论文写作课资料。",
        introLines: [
            "写作阶段、稿件问题，直接问。",
            "讨论 draft 时带上卡点。",
        ],
        quickActions: [
            { label: "问课程讲次", question: "论文写作课第 7 讲主要讲什么？", context: "论文写作课" },
            { label: "问写作卡点", question: "我在写 related work，通常应该先检查哪些问题？", context: "论文写作课" },
            { label: "约论文讨论", question: "我想约时间讨论论文提纲，需要先准备哪些材料？", context: "论文写作课" },
        ],
    },
    lab_member: {
        label: "课题组学生",
        defaultContext: "科研指导",
        defaultQuestion: "我上次提到的研究主题和 blocker 是什么？",
        placeholder: "写研究主题、blocker 或组会任务。",
        drawerHint: "优先参考研究和组内记录。",
        introLines: [
            "研究进展、blocker、组会准备，直接问。",
            "预约请带本周推进和 draft。",
        ],
        quickActions: [
            { label: "接着上次进展", question: "我上次提到的研究主题和 blocker 是什么？", context: "科研指导" },
            { label: "问组会准备", question: "下次组会前我应该准备哪些材料？", context: "组会准备" },
            { label: "梳理研究重点", question: "帮我梳理一下这周的研究推进重点。", context: "科研指导" },
        ],
    },
};
const adminOnlyDrawerButtons = [
    openKnowledgeButton,
    openAvailabilityEditorButton,
    openBookingListButton,
    openEscalationQueueButton,
    openMemoryProfilesButton,
    openOperationsConsoleButton,
    openQuestionAnalyticsButton,
].filter(Boolean);
const adminOnlyModals = [
    knowledgeModal,
    availabilityModal,
    bookingAdminModal,
    escalationAdminModal,
    memoryProfilesModal,
    operationsConsoleModal,
    questionAnalyticsModal,
].filter(Boolean);
const overlayModals = [
    identityModal,
    knowledgeModal,
    bookingModal,
    suggestionModal,
    adminLoginModal,
    userRegisterModal,
    userLoginModal,
    availabilityModal,
    bookingAdminModal,
    escalationAdminModal,
    memoryProfilesModal,
    operationsConsoleModal,
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
chatStream?.addEventListener("click", handleIntroQuickActionClick);
chatStream?.addEventListener("click", handleCopyAnswerClick);
historyList?.addEventListener("click", handleConversationHistoryClick);
historyRailToggleButton?.addEventListener("click", toggleHistoryRail);
topbarHistoryToggleButton?.addEventListener("click", toggleHistoryRail);
topbarMobileHistoryToggleButton?.addEventListener("click", toggleHistoryRail);
topbarNewChatButton?.addEventListener("click", startFreshConversation);
topbarActionsToggleButton?.addEventListener("click", toggleMobileTopbarActions);
topbarActions?.addEventListener("click", handleTopbarActionsClick);
historyNewChatButton?.addEventListener("click", () => {
    startFreshConversation();
});
composerUploadButton?.addEventListener("click", () => chatFileInput?.click());
chatFileInput?.addEventListener("change", handleChatFileSelection);
composerAttachmentList?.addEventListener("click", handleComposerAttachmentAction);

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
globalThis.document?.addEventListener("visibilitychange", () => {
    if (globalThis.document.visibilityState === "visible") {
        sendOnlinePresenceHeartbeat({ silent: true });
    }
});
visitorProfileInput?.addEventListener("change", handleVisitorProfileChange);
identityModal?.addEventListener("click", handleIdentityChoiceClick);
document.getElementById("identity-user-login")?.addEventListener("click", () => {
    markVisitorIdentitySelected();
    closeModals();
    openModal(userLoginModal);
});
document.getElementById("identity-admin-login")?.addEventListener("click", () => {
    markVisitorIdentitySelected();
    closeModals();
    openModal(adminLoginModal);
});

document.getElementById("open-settings-drawer")?.addEventListener("click", openSettingsDrawer);
document.getElementById("open-status-drawer")?.addEventListener("click", openStatusDrawer);
topbarUserBadge?.addEventListener("click", openSettingsDrawer);
document.querySelectorAll("[data-close-drawer]").forEach((button) => {
    button.addEventListener("click", closeSettingsDrawer);
});
document.querySelectorAll("[data-close-status-drawer]").forEach((button) => {
    button.addEventListener("click", closeStatusDrawer);
});
document.getElementById("open-user-register")?.addEventListener("click", () => {
    prepareUserRegistrationForm();
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
openSuggestionsButton?.addEventListener("click", async () => {
    closeDrawer();
    openModal(suggestionModal);
    await loadSuggestionList();
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
document.getElementById("open-operations-console")?.addEventListener("click", async () => {
    if (!ensureAdminOnlyAccess({ openLogin: true })) {
        return;
    }
    closeDrawer();
    openModal(operationsConsoleModal);
    await loadOperationsWorkbench();
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
document.getElementById("refresh-operations-console")?.addEventListener("click", async () => {
    await loadOperationsWorkbench();
});
memoryProfilesCategoryFilter?.addEventListener("change", async () => {
    await loadMemoryProfiles();
});
questionAnalyticsWindow?.addEventListener("change", async () => {
    await loadQuestionAnalytics();
});
operationsWindow?.addEventListener("change", async () => {
    await loadOperationsWorkbench();
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
operationsGaps?.addEventListener("click", handleKnowledgeGapDraftAction);
operationsArtifactDrafts?.addEventListener("click", handleArtifactDraftAction);
operationsQueues?.addEventListener("click", handleOperationsQueueAction);
operationsTasks?.addEventListener("click", handleOperationsTaskAction);
modalOverlay.addEventListener("click", handleModalOverlayClick);
document.addEventListener("click", handleOutsideDrawerClick);
document.querySelectorAll("[data-close-modal]").forEach((button) => {
    button.addEventListener("click", closeModals);
});
bookingList.addEventListener("click", handleBookingApprovalClick);
escalationList?.addEventListener("click", handleEscalationResolveClick);
availabilityGrid.addEventListener("click", handleAvailabilityGridClick);

document.getElementById("load-demo-chat").addEventListener("click", () => {
    const profileConfig = getVisitorProfileConfig();
    seedChatQuestion(profileConfig.defaultQuestion, profileConfig.defaultContext);
    closeDrawer();
});

document.getElementById("refresh-knowledge").addEventListener("click", async () => {
    await loadKnowledgeList();
});
document.getElementById("refresh-suggestions")?.addEventListener("click", async () => {
    await loadSuggestionList();
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
                visitor_profile: userRegisterProfileInput?.value || "",
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

    noteOutgoingConversationQuestion(question);

    const payload = {
        student_name: document.getElementById("student-name").value,
        student_email: document.getElementById("student-email").value || null,
        course_context: document.getElementById("course-context").value || null,
        visitor_profile: visitorProfileInput?.value || null,
        question,
        conversation_id: activeConversationId,
        deep_thinking: deepThinkingCheckbox?.checked ?? false,
        deep_thinking_explicit: deepThinkingExplicitlyEnabled,
    };
    const submittedFiles = [...pendingChatAttachments];
    const submittedAttachments = submittedFiles.map((file) => ({
        fileName: file.name,
        sizeBytes: file.size,
    }));
    const workflowRequestId = createConversationId();

    appendMessage("user", payload.student_name || "学生", question, {
        emphasis: "user",
        attachments: submittedAttachments,
    });
    const pendingMessage = appendMessage("assistant", assistantLabel, "正在整理问题、检索资料并准备回复", {
        state: "pending",
    });
    renderPendingAssistantMessage(pendingMessage, "理解问题", []);
    persistActiveConversationSnapshot();
    const requestBody = buildChatRequestBody(payload, submittedFiles);
    document.getElementById("chat-question").value = "";
    clearPendingChatAttachments();
    autoResizeTextarea();
    chatSubmitButton.disabled = true;
    chatSubmitButton.textContent = "发送中";
    let workflowRequestIdActive = workflowRequestId;
    await openWorkflowTraceStream(workflowRequestIdActive);

    let attempt = 0;
    const maxAttempts = submittedFiles.length === 0 ? 2 : 1;
    while (true) {
        attempt += 1;
        try {
            const data = await apiRequest(`/chat?request_id=${encodeURIComponent(workflowRequestIdActive)}`, {
                method: "POST",
                body: requestBody,
                timeoutMs: 120000,
            });
            activeConversationId = data.conversation_id || activeConversationId;
            stopWorkflowTraceStream();
            renderWorkflowTrace(data.workflow_trace || [], {
                workflowAction: data.workflow_action || null,
                knowledgeHits: Array.isArray(data.knowledge_hits) ? data.knowledge_hits.length : null,
                isStreaming: false,
                plannerPreview: data.planner_preview || null,
                shadowPlannerPreview: data.shadow_planner_preview || null,
                plannerComparison: data.planner_comparison || null,
            });
            renderAssistantMessage(
                pendingMessage,
                data.answer,
                data.answer_basis || [],
                data.follow_up_actions || [],
                data.knowledge_hits || [],
                data.booking_result || null,
                false,
                data.exchange_id || null,
                data.workflow_trace || []
            );
            noteConversationAnswerPreview(data.answer);
            persistActiveConversationSnapshot();
            void syncConversationHistoryFromServer();
            break;
        } catch (error) {
            const canRetry =
                attempt < maxAttempts &&
                error?.status === 504 &&
                submittedFiles.length === 0;
            if (canRetry) {
                stopWorkflowTraceStream();
                workflowRequestIdActive = createConversationId();
                renderPendingAssistantMessage(
                    pendingMessage,
                    "后端响应超时，正在自动重试…",
                    []
                );
                await new Promise((resolve) => globalThis.setTimeout(resolve, 1500));
                await openWorkflowTraceStream(workflowRequestIdActive);
                continue;
            }
            stopWorkflowTraceStream();
            renderWorkflowTraceError(error.message);
            renderAssistantMessage(pendingMessage, error.message, [], [], [], null, true, null, activeWorkflowSteps);
            noteConversationAnswerPreview(error.message);
            persistActiveConversationSnapshot();
            break;
        }
    }
    chatSubmitButton.disabled = false;
    chatSubmitButton.textContent = "发送";
});

function getChatAttachmentKey(file) {
    return `${file.name}:${file.size}:${file.lastModified}`;
}

function buildChatRequestBody(payload, attachments = []) {
    if (!attachments.length) {
        return JSON.stringify(payload);
    }

    const formData = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== "") {
            formData.append(key, String(value));
        }
    });
    attachments.forEach((file) => {
        formData.append("files", file, file.name);
    });
    return formData;
}

function formatAttachmentSize(sizeBytes) {
    if (typeof sizeBytes !== "number" || Number.isNaN(sizeBytes) || sizeBytes <= 0) {
        return "";
    }
    if (sizeBytes < 1024) {
        return `${sizeBytes} B`;
    }
    if (sizeBytes < 1024 * 1024) {
        return `${(sizeBytes / 1024).toFixed(1)} KB`;
    }
    return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

function setComposerUploadHint(message = DEFAULT_COMPOSER_UPLOAD_HINT, state = "normal") {
    if (!composerUploadHint) {
        return;
    }
    composerUploadHint.textContent = message;
    composerUploadHint.classList.toggle("composer-upload-hint-error", state === "error");
}

function isSupportedChatAttachmentFile(file) {
    const suffix = file.name.includes(".") ? `.${file.name.split(".").pop().toLowerCase()}` : "";
    return SUPPORTED_CHAT_UPLOAD_SUFFIXES.has(suffix) || String(file.type || "").toLowerCase().startsWith("text/");
}

function renderComposerAttachmentList() {
    if (!composerAttachmentList) {
        return;
    }
    if (!pendingChatAttachments.length) {
        composerAttachmentList.hidden = true;
        composerAttachmentList.innerHTML = "";
        setComposerUploadHint();
        return;
    }

    composerAttachmentList.hidden = false;
    composerAttachmentList.innerHTML = pendingChatAttachments
        .map((file) => `
            <span class="attachment-chip attachment-chip-editable" data-chat-file-key="${escapeHtml(getChatAttachmentKey(file))}">
                <span class="attachment-chip-copy">
                    <strong>${escapeHtml(file.name)}</strong>
                    <small>${escapeHtml(formatAttachmentSize(file.size))}</small>
                </span>
                <button type="button" class="attachment-chip-remove" data-remove-chat-file="${escapeHtml(getChatAttachmentKey(file))}" aria-label="移除 ${escapeHtml(file.name)}">×</button>
            </span>
        `)
        .join("");
    setComposerUploadHint(`已选中 ${pendingChatAttachments.length} 个附件。`);
}

function clearPendingChatAttachments() {
    pendingChatAttachments = [];
    if (chatFileInput) {
        chatFileInput.value = "";
    }
    renderComposerAttachmentList();
}

function handleComposerAttachmentAction(event) {
    const button = event.target.closest("[data-remove-chat-file]");
    if (!button) {
        return;
    }
    const targetKey = button.dataset.removeChatFile || "";
    pendingChatAttachments = pendingChatAttachments.filter((file) => getChatAttachmentKey(file) !== targetKey);
    renderComposerAttachmentList();
}

function handleChatFileSelection(event) {
    const files = Array.from(event.target.files || []);
    if (!files.length) {
        return;
    }

    const nextAttachments = [...pendingChatAttachments];
    let errorMessage = "";
    for (const file of files) {
        if (!isSupportedChatAttachmentFile(file)) {
            errorMessage = `暂只支持 PDF、TXT、MD、CSV、JSON、PY、YAML、LOG 文件：${file.name}`;
            continue;
        }
        if (file.size > MAX_CHAT_UPLOAD_BYTES) {
            errorMessage = `附件超过 5MB 限制：${file.name}`;
            continue;
        }
        if (nextAttachments.length >= MAX_CHAT_UPLOAD_FILES) {
            errorMessage = `一次最多上传 ${MAX_CHAT_UPLOAD_FILES} 个附件。`;
            break;
        }
        const key = getChatAttachmentKey(file);
        if (nextAttachments.some((item) => getChatAttachmentKey(item) === key)) {
            continue;
        }
        nextAttachments.push(file);
    }

    pendingChatAttachments = nextAttachments;
    if (chatFileInput) {
        chatFileInput.value = "";
    }
    renderComposerAttachmentList();
    if (errorMessage) {
        setComposerUploadHint(errorMessage, "error");
    }
}

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

suggestionForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const messageInput = document.getElementById("suggestion-message");
    const categoryInput = document.getElementById("suggestion-category");
    const message = messageInput.value.trim();
    if (!message) {
        return;
    }

    setInlineStatus(suggestionResponse, "正在匿名提交留言...", "empty");
    try {
        await apiRequest("/suggestions", {
            method: "POST",
            body: JSON.stringify({
                message,
                category: categoryInput.value || null,
            }),
        });
        messageInput.value = "";
        setInlineStatus(suggestionResponse, "留言已提交，感谢你的建议。", "success");
        await refreshStatus();
        await loadSuggestionList();
    } catch (error) {
        setInlineStatus(suggestionResponse, error.message, "error");
    }
});

chatQuestion.addEventListener("input", () => {
    if (chatQuestion.value.trim() !== lastAutoChatQuestion) {
        lastAutoChatQuestion = "";
    }
    autoResizeTextarea();
});
courseContextInput?.addEventListener("input", updateComposerContextChips);
chatQuestion.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" || event.shiftKey || event.isComposing) {
        return;
    }
    event.preventDefault();
    chatForm.requestSubmit(chatSubmitButton);
});

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

function handleVisitorProfileChange() {
    markVisitorIdentitySelected(visitorProfileInput?.value);
    syncUserRegisterProfileFromVisitorProfile();
    applyVisitorProfilePresentation({ syncCourseContext: true });
}

function syncUserRegisterProfileFromVisitorProfile() {
    if (!userRegisterProfileInput || !visitorProfileInput) {
        return;
    }
    userRegisterProfileInput.value = visitorProfileInput.value;
}

function prepareUserRegistrationForm() {
    syncUserRegisterProfileFromVisitorProfile();
    userRegisterResponse.textContent = "注册后会自动登录当前账号，并固定你的访问身份。";
    userRegisterResponse.className = "inline-status inline-status-empty";
}

function handleIdentityChoiceClick(event) {
    const trigger = event.target.closest("[data-identity-profile]");
    if (!(trigger instanceof HTMLElement)) {
        return;
    }
    const profile = trigger.dataset.identityProfile;
    if (!profile || !VISITOR_PROFILE_CONFIGS[profile] || !visitorProfileInput) {
        return;
    }
    visitorProfileInput.value = profile;
    markVisitorIdentitySelected(profile);
    syncUserRegisterProfileFromVisitorProfile();
    applyVisitorProfilePresentation({ syncCourseContext: true });
    closeModals();
    chatQuestion?.focus();
}

function markVisitorIdentitySelected(profile = visitorProfileInput?.value) {
    try {
        globalThis.localStorage?.setItem(VISITOR_IDENTITY_SELECTED_KEY, "true");
        if (profile && VISITOR_PROFILE_CONFIGS[profile]) {
            globalThis.localStorage?.setItem(VISITOR_PROFILE_STORAGE_KEY, profile);
        }
    } catch (error) {
        // Browser privacy modes may block localStorage; the selected profile still applies in memory.
    }
}

function getStoredVisitorProfile() {
    try {
        const profile = globalThis.localStorage?.getItem(VISITOR_PROFILE_STORAGE_KEY) || "";
        return VISITOR_PROFILE_CONFIGS[profile] ? profile : "";
    } catch (error) {
        return "";
    }
}

function applyStoredVisitorProfile() {
    const profile = getStoredVisitorProfile();
    if (profile && visitorProfileInput) {
        visitorProfileInput.value = profile;
        syncUserRegisterProfileFromVisitorProfile();
    }
}

function shouldPromptForVisitorIdentity() {
    if (isAdminSession || isUserAuthenticated || !identityModal) {
        return false;
    }
    try {
        return globalThis.localStorage?.getItem(VISITOR_IDENTITY_SELECTED_KEY) !== "true";
    } catch (error) {
        return true;
    }
}

function hasActiveOverlaySurface() {
    return [
        settingsDrawer,
        statusDrawer,
        identityModal,
        knowledgeModal,
        bookingModal,
        suggestionModal,
        adminLoginModal,
        userRegisterModal,
        userLoginModal,
        availabilityModal,
        bookingAdminModal,
        escalationAdminModal,
        memoryProfilesModal,
        operationsConsoleModal,
        questionAnalyticsModal,
    ].some(isOverlayElementVisible);
}

function isOverlayElementVisible(element) {
    return Boolean(element && !element.classList.contains("hidden"));
}

function maybeOpenVisitorIdentityPrompt() {
    if (shouldPromptForVisitorIdentity() && !hasActiveOverlaySurface()) {
        openModal(identityModal);
    }
}

function isVisitorIdentityPromptOpen() {
    return isOverlayElementVisible(identityModal);
}

function handleModalOverlayClick() {
    if (isVisitorIdentityPromptOpen()) {
        return;
    }
    closeModals();
}

function handleOutsideDrawerClick(event) {
    const target = event.target;
    if (!(target instanceof Element)) {
        return;
    }

    if (
        !document.body.classList.contains("history-rail-collapsed")
        && !target.closest(".history-rail")
        && !target.closest("#history-rail-toggle")
        && !target.closest("#topbar-mobile-history-toggle")
        && !target.closest("#topbar-history-toggle")
    ) {
        setHistoryRailCollapsed(true);
    }

    if (isMobileTopbarActionsOpen() && topbarShell && !topbarShell.contains(target)) {
        closeMobileTopbarActions();
    }

    if (!isStatusDrawerClosed()) {
        if (!statusDrawer?.contains(target) && !target.closest("#open-status-drawer")) {
            closeStatusDrawer();
        }
    }

    if (!isSettingsDrawerClosed()) {
        if (
            !settingsDrawer?.contains(target)
            && !target.closest("#open-settings-drawer")
            && !target.closest("#topbar-user-badge")
        ) {
            closeSettingsDrawer();
        }
    }
}

function getVisitorProfileConfig(profile = visitorProfileInput?.value) {
    return VISITOR_PROFILE_CONFIGS[profile] || VISITOR_PROFILE_CONFIGS.general_visitor;
}

function setMultilineText(element, lines) {
    if (!element) {
        return;
    }
    element.replaceChildren();
    lines.forEach((line, index) => {
        if (index > 0) {
            element.append(document.createElement("br"));
        }
        element.append(document.createTextNode(line));
    });
}

function updateIntroQuickActions(config) {
    const introQuickActionButtons = Array.from(document.querySelectorAll(".intro-chip-button"));
    introQuickActionButtons.forEach((button, index) => {
        const action = config.quickActions[index];
        if (!action) {
            button.hidden = true;
            return;
        }
        button.hidden = false;
        button.textContent = action.label;
        button.dataset.seedQuestion = action.question;
        button.dataset.seedContext = action.context;
    });
}

function updateProfileDrawerCopy(config) {
    if (!profileDrawerCopy) {
        return;
    }
    const accountLead = isUserAuthenticated
        ? "当前已绑定登录账号。"
        : "先把姓名和邮箱填对。";
    profileDrawerCopy.textContent = `${accountLead}${config.drawerHint}`;
}

function updateComposerContextChips() {
    const config = getVisitorProfileConfig();
    if (composerProfileChip) {
        composerProfileChip.textContent = `身份：${config.label}`;
    }
    if (composerContextChip) {
        composerContextChip.textContent = `场景：${courseContextInput?.value?.trim() || config.defaultContext}`;
    }
    if (composerWorkflowChip) {
        composerWorkflowChip.textContent = latestWorkflowMeta.isStreaming
            ? `处理：${formatWorkflowActionLabel(latestWorkflowMeta, activeWorkflowSteps)}`
            : "处理：检索与整理";
    }
}

function applyVisitorProfilePresentation({ syncCourseContext = false } = {}) {
    const config = getVisitorProfileConfig();
    setMultilineText(document.querySelector(".intro-card .message-body"), config.introLines);
    updateIntroQuickActions(config);
    updateProfileDrawerCopy(config);

    if (chatQuestion) {
        chatQuestion.placeholder = config.placeholder;
        const currentQuestion = chatQuestion.value.trim();
        if (!currentQuestion || currentQuestion === lastAutoChatQuestion) {
            chatQuestion.value = config.defaultQuestion;
            lastAutoChatQuestion = config.defaultQuestion;
            autoResizeTextarea();
        }
    }

    if (courseContextInput && (syncCourseContext || !courseContextInput.value.trim())) {
        const currentContext = courseContextInput.value.trim();
        if (!currentContext || currentContext === lastAutoCourseContext) {
            courseContextInput.value = config.defaultContext;
            lastAutoCourseContext = config.defaultContext;
        }
    }
    updateComposerContextChips();
}

function markPresentationReady() {
    document.body?.classList.remove("presentation-booting");
}

function seedChatQuestion(question, courseContext = "") {
    chatQuestion.value = question;
    lastAutoChatQuestion = "";
    if (courseContextInput && courseContext) {
        courseContextInput.value = courseContext;
        lastAutoCourseContext = courseContext;
    }
    autoResizeTextarea();
    chatQuestion.focus();
}

async function refreshStatus() {
    const fetchHealthSnapshot = async () => {
        let lastError = null;
        for (let attempt = 0; attempt <= HEALTH_REQUEST_RETRY_COUNT; attempt += 1) {
            try {
                return await apiRequest("/health", { timeoutMs: HEALTH_REQUEST_TIMEOUT_MS });
            } catch (error) {
                lastError = error;
            }
        }
        throw lastError;
    };

    try {
        const data = await fetchHealthSnapshot();
        lastHealthyStatusSnapshot = data;
        lastHealthyStatusAt = Date.now();
        applyBranding(data.owner_name, data.owner_role, data.homepage_public_url);
        statusPill.textContent = data.status === "ok" ? "服务正常" : `状态 ${data.status}`;
        modelPill.textContent = "连接已就绪";
        knowledgePill.textContent = `知识库 ${data.knowledge_documents}`;
        renderTopbarLiveStatus(data);
        renderOnlineOverview(data);
    } catch (error) {
        const hasRecentSnapshot =
            lastHealthyStatusSnapshot
            && Date.now() - lastHealthyStatusAt <= HEALTH_SNAPSHOT_STALE_MS;
        if (hasRecentSnapshot) {
            const cached = lastHealthyStatusSnapshot;
            applyBranding(cached.owner_name, cached.owner_role, cached.homepage_public_url);
            statusPill.textContent = "服务延迟";
            modelPill.textContent = "连接较慢";
            knowledgePill.textContent = `知识库 ${cached.knowledge_documents}`;
            renderTopbarLiveStatus(cached);
            renderOnlineOverview(cached, "状态刷新较慢，当前显示最近一次成功快照。");
            return;
        }
        applyBranding(null, null, "");
        statusPill.textContent = "服务不可用";
        modelPill.textContent = "连接状态未知";
        knowledgePill.textContent = "知识库未知";
        renderTopbarLiveStatus(null);
        renderOnlineOverview(null, error.message);
    }
}

function renderTopbarLiveStatus(data) {
    if (!topbarServiceStatus || !topbarUserCount || !topbarQuestionCount || !topbarModelStatus) {
        return;
    }
    if (!data) {
        renderTopbarLiveItem(topbarServiceStatus, "服务", "不可用", "请稍后刷新");
        renderTopbarLiveItem(topbarUserCount, "在线用户", "--", "暂无统计");
        renderTopbarLiveItem(topbarQuestionCount, "累计问答", "--", "暂无统计");
        renderTopbarLiveItem(topbarModelStatus, "模型请求", "未知", "未读取到运行数据");
        renderTopbarStatusSummary("运行信息：暂时不可用");
        return;
    }
    const modelSummary = buildModelRuntimeSummary(data);
    const onlineVisitors = formatCount(data.online_visitors);
    const onlineUsers = formatCount(data.online_authenticated_users);
    renderTopbarLiveItem(topbarServiceStatus, "服务", data.status === "ok" ? "在线" : data.status, data.sage_runtime || "SAGE runtime");
    renderTopbarLiveItem(topbarUserCount, "在线用户", onlineVisitors, `登录 ${onlineUsers}`);
    renderTopbarLiveItem(topbarQuestionCount, "累计问答", formatCount(data.conversation_memory_records), "聊天记忆记录");
    renderTopbarLiveItem(topbarModelStatus, "模型请求", modelSummary.headline, modelSummary.detail);
    renderTopbarStatusSummary(`运行信息：${data.status === "ok" ? "服务在线" : `状态 ${data.status}`} · 在线 ${onlineVisitors} · 累计 ${formatCount(data.conversation_memory_records)} 问答`);
}

function renderTopbarStatusSummary(text) {
    if (topbarStatusSummary) {
        topbarStatusSummary.textContent = text;
    }
}

function renderTopbarLiveItem(element, label, value, detail = "") {
    element.innerHTML = `
        <small>${escapeHtml(label)}</small>
        <strong>${escapeHtml(String(value))}</strong>
        ${detail ? `<em>${escapeHtml(detail)}</em>` : ""}
    `;
}

function renderOnlineOverview(data, errorMessage = "") {
    if (!onlineOverviewGrid || !onlineOverviewCopy) {
        return;
    }
    if (!data) {
        onlineOverviewGrid.innerHTML = [
            ["在线访客", "--"],
            ["在线账号", "--"],
            ["累计询问", "--"],
            ["模型状态", "未知"],
            ["活跃会话", "--"],
        ].map(renderOnlineOverviewItem).join("");
        onlineOverviewCopy.textContent = errorMessage || "暂时无法读取在线统计。";
        renderOnlineBenchmarkTable(null);
        return;
    }

    const modelSummary = buildModelRuntimeSummary(data);
    const onlineWindowSeconds = Number(data.online_window_seconds || 300);
    const onlineWindowMinutes = Math.max(1, Math.round(onlineWindowSeconds / 60));
    const entries = [
        ["在线访客", `${formatCount(data.online_visitors)} 人`],
        ["在线账号", `${formatCount(data.online_authenticated_users)} 人`],
        ["活跃会话", `${formatCount(data.online_active_conversations)} 个`],
        ["注册用户", `${formatCount(data.registered_user_accounts)} 个账号`],
        ["累计问答", `${formatCount(data.conversation_memory_records)} 条记录`],
        ["知识库资料", `${formatCount(data.knowledge_documents)} 篇`],
        ["待跟进事项", `${formatCount(data.follow_up_dispatch_due)} 个`],
        ["模型名称", data.model_name || "未配置"],
        ["模型请求", modelSummary.headline],
        ["成功率", modelSummary.successRate],
        ["最近成功", modelSummary.lastSuccess],
    ];
    onlineOverviewGrid.innerHTML = entries.map(renderOnlineOverviewItem).join("");
    const runtime = data.sage_runtime || "SAGE runtime";
    onlineOverviewCopy.textContent = `${runtime} · 在线窗口 ${onlineWindowMinutes} 分钟 · ${modelSummary.detail} · 缓存项 ${formatCount(data.llm_cache_entries)}，缓存命中 ${formatCount(data.llm_cache_hit_count)} 次。`;
    renderOnlineBenchmarkTable(data);
}

function renderOnlineBenchmarkTable(data) {
    if (!onlineBenchmarkTable) {
        return;
    }

    if (!data) {
        onlineBenchmarkTable.innerHTML = '<div class="online-benchmark-empty">暂时无法读取推理指标。</div>';
        return;
    }

    const requestCount = toCountNumber(data.llm_request_count);
    const successCount = toCountNumber(data.llm_success_count);
    const errorCount = toCountNumber(data.llm_error_count);
    const cacheHitCount = toCountNumber(data.llm_cache_hit_count);
    const cacheEntries = toCountNumber(data.llm_cache_entries);
    const appCacheHitRate = Number(data.llm_app_cache_hit_rate || 0);
    const semanticCacheHitRate = Number(data.llm_semantic_cache_hit_rate || 0);
    const vllmPrefixCacheHitRate = Number(data.llm_vllm_prefix_cache_hit_rate || 0);
    const vllmPrefixQueries = toCountNumber(data.llm_vllm_prefix_cache_queries);
    const vllmPrefixHits = toCountNumber(data.llm_vllm_prefix_cache_hits);
    const plannerTotal = toCountNumber(data.planner_deterministic_total);
    const plannerFallbacks = toCountNumber(data.planner_deterministic_fallbacks);
    const plannerShadowErrors = toCountNumber(data.planner_shadow_errors);
    const avgDetLatency = Number(data.planner_avg_deterministic_latency_ms || 0);
    const avgShadowLatency = Number(data.planner_avg_shadow_latency_ms || 0);
    const avgLlmLatency = Number(data.llm_avg_latency_ms || 0);
    const p95LikeLlmLatency = Number(data.llm_max_latency_ms || 0);
    const llmRps = Number(data.llm_request_throughput_rps || 0);
    const llmTps = Number(data.llm_completion_throughput_tps || 0);
    const completionTokens = toCountNumber(data.llm_completion_tokens_total);
    const successRate = requestCount > 0 ? `${Math.round((successCount / requestCount) * 100)}%` : "--";
    const cacheHitRate = requestCount > 0 ? `${Math.round((cacheHitCount / requestCount) * 100)}%` : "--";
    const fallbackRate = plannerTotal > 0 ? `${Math.round((plannerFallbacks / plannerTotal) * 100)}%` : "--";

    const rows = [
        ["模型状态", formatLlmStatus(data.llm_status, errorCount)],
        ["请求总数", formatCount(requestCount)],
        ["成功数 / 失败数", `${formatCount(successCount)} / ${formatCount(errorCount)}`],
        ["成功率", successRate],
        ["吞吐（请求/s）", llmRps > 0 ? llmRps.toFixed(3) : "0.000"],
        ["吞吐（Token/s）", llmTps > 0 ? llmTps.toFixed(2) : "0.00"],
        ["平均 LLM 延迟", Number.isFinite(avgLlmLatency) ? `${avgLlmLatency.toFixed(2)} ms` : "--"],
        ["峰值 LLM 延迟", Number.isFinite(p95LikeLlmLatency) ? `${p95LikeLlmLatency.toFixed(2)} ms` : "--"],
        ["缓存命中率（总）", cacheHitRate],
        ["应用缓存命中率", formatPercentage(appCacheHitRate)],
        ["语义缓存命中率", formatPercentage(semanticCacheHitRate)],
        ["vLLM 前缀命中率", formatPercentage(vllmPrefixCacheHitRate)],
        ["vLLM 前缀命中（命中/查询）", `${formatCount(vllmPrefixHits)} / ${formatCount(vllmPrefixQueries)}`],
        ["缓存条目", formatCount(cacheEntries)],
        ["累计输出 Token", formatCount(completionTokens)],
        ["规划总次数", formatCount(plannerTotal)],
        ["规划回退率", fallbackRate],
        ["Shadow 错误", formatCount(plannerShadowErrors)],
        ["平均规划延迟", Number.isFinite(avgDetLatency) ? `${avgDetLatency.toFixed(2)} ms` : "--"],
        ["平均 Shadow 延迟", Number.isFinite(avgShadowLatency) ? `${avgShadowLatency.toFixed(2)} ms` : "--"],
        ["最近成功", formatMetricTimestamp(data.llm_last_success_at)],
    ];

    onlineBenchmarkTable.innerHTML = rows
        .map(([label, value]) => `
            <div class="online-benchmark-row">
                <span class="online-benchmark-label">${escapeHtml(label)}</span>
                <strong class="online-benchmark-value">${escapeHtml(String(value))}</strong>
            </div>
        `)
        .join("");
}

function resolveOnlinePresenceClientId() {
    try {
        const existing = globalThis.localStorage?.getItem(ONLINE_PRESENCE_CLIENT_KEY);
        if (existing && existing.trim()) {
            return existing;
        }
        const created = createConversationId();
        globalThis.localStorage?.setItem(ONLINE_PRESENCE_CLIENT_KEY, created);
        return created;
    } catch {
        return createConversationId();
    }
}

function resolvePresenceEmail() {
    if (isUserAuthenticated && currentUserAccountEmail) {
        return currentUserAccountEmail;
    }
    const rawEmail = studentEmailInput?.value?.trim();
    if (!rawEmail) {
        return "";
    }
    return rawEmail.toLowerCase();
}

async function sendOnlinePresenceHeartbeat({ silent = true } = {}) {
    const payload = {
        client_id: resolveOnlinePresenceClientId(),
        conversation_id: activeConversationId || "",
        student_email: resolvePresenceEmail(),
        is_authenticated: Boolean(isUserAuthenticated),
    };
    try {
        return await apiRequest("/presence/heartbeat", {
            method: "POST",
            body: JSON.stringify(payload),
            timeoutMs: 5000,
        });
    } catch (error) {
        if (!silent) {
            console.warn("presence heartbeat failed", error);
        }
        return null;
    }
}

function startOnlinePresenceHeartbeat() {
    if (onlinePresenceHeartbeatTimer !== null) {
        globalThis.clearInterval(onlinePresenceHeartbeatTimer);
        onlinePresenceHeartbeatTimer = null;
    }

    sendOnlinePresenceHeartbeat({ silent: true });
    onlinePresenceHeartbeatTimer = globalThis.setInterval(() => {
        if (globalThis.document?.visibilityState === "hidden") {
            return;
        }
        sendOnlinePresenceHeartbeat({ silent: true });
    }, ONLINE_PRESENCE_INTERVAL_MS);
}

function startStatusAutoRefresh() {
    if (statusRefreshTimer !== null) {
        globalThis.clearInterval(statusRefreshTimer);
        statusRefreshTimer = null;
    }
    statusRefreshTimer = globalThis.setInterval(() => {
        if (globalThis.document?.visibilityState === "hidden") {
            return;
        }
        refreshStatus();
    }, STATUS_REFRESH_INTERVAL_MS);
}

function renderOnlineOverviewItem([label, value]) {
    return `
        <article class="online-overview-item">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(String(value))}</strong>
        </article>
    `;
}

function formatLlmStatus(status, errorCount) {
    if (status === "ok") {
        return "可用";
    }
    if (status === "error") {
        return `异常 ${formatCount(errorCount)}`;
    }
    return "未调用";
}

function buildModelRuntimeSummary(data) {
    const requestCount = toCountNumber(data.llm_request_count);
    const successCount = toCountNumber(data.llm_success_count);
    const errorCount = toCountNumber(data.llm_error_count);
    const statusLabel = formatLlmStatus(data.llm_status, errorCount);
    const successRate = requestCount > 0 ? `${Math.round((successCount / requestCount) * 100)}%` : "暂无请求";
    const headline = requestCount > 0
        ? `${successCount}/${requestCount} 成功`
        : statusLabel;
    const detail = requestCount > 0
        ? `${statusLabel} · 失败 ${formatCount(errorCount)} 次`
        : "还没有新的模型请求";
    return {
        headline,
        detail,
        successRate,
        lastSuccess: formatMetricTimestamp(data.llm_last_success_at),
    };
}

function toCountNumber(value) {
    const numeric = Number(value || 0);
    if (!Number.isFinite(numeric) || numeric < 0) {
        return 0;
    }
    return numeric;
}

function formatMetricTimestamp(value) {
    if (!value) {
        return "暂无记录";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "暂无记录";
    }
    return new Intl.DateTimeFormat("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    }).format(date);
}

function formatCount(value) {
    const numeric = Number(value || 0);
    if (!Number.isFinite(numeric)) {
        return "0";
    }
    return new Intl.NumberFormat("zh-CN").format(numeric);
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
        openOperationsConsoleButton?.classList.toggle("hidden", !isAdmin);
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
        openOperationsConsoleButton?.classList.add("hidden");
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
    await syncConversationHistoryFromServer();
}

function applyUserSession(session) {
    const wasAuthenticated = isUserAuthenticated;
    const authenticated = Boolean(session?.is_authenticated && session?.account);
    isUserAuthenticated = authenticated;
    currentUserAccountEmail = authenticated ? String(session.account?.email || "").trim().toLowerCase() : "";

    userAuthPanel?.classList.toggle("hidden", authenticated);
    userSessionPanel?.classList.toggle("hidden", !authenticated);

    if (authenticated) {
        const account = session.account;
        userSessionCopy.textContent = `当前账号：${account.name} · ${account.email}`;
        if (topbarUserBadge) {
            topbarUserBadge.classList.remove("hidden");
            const profileLabel = VISITOR_PROFILE_CONFIGS[account.visitor_profile]?.label || "已登录";
            topbarUserBadge.title = `${account.name} · ${account.email}`;
            topbarUserBadge.setAttribute("aria-label", `当前账号：${account.name}，${profileLabel}`);
            const labelEl = topbarUserBadge.querySelector(".topbar-user-badge-label");
            if (labelEl) {
                labelEl.textContent = profileLabel;
            }
            const avatarEl = topbarUserBadge.querySelector(".topbar-user-badge-avatar");
            if (avatarEl) {
                const initial = (account.name || "?").trim().charAt(0).toUpperCase() || "U";
                avatarEl.textContent = initial;
            }
        }
        if (topbarUserBadgeName) {
            topbarUserBadgeName.textContent = account.name;
        }
        studentNameInput.value = account.name;
        studentEmailInput.value = account.email;
        bookingStudentNameInput.value = account.name;
        bookingEmailInput.value = account.email;
        if (account.visitor_profile && VISITOR_PROFILE_CONFIGS[account.visitor_profile] && visitorProfileInput) {
            visitorProfileInput.value = account.visitor_profile;
            syncUserRegisterProfileFromVisitorProfile();
            markVisitorIdentitySelected(account.visitor_profile);
        }
        studentNameInput.readOnly = true;
        studentEmailInput.readOnly = true;
        applyVisitorProfilePresentation();
        switchConversationHistoryScope(resolveConversationHistoryStorageScope());
        return;
    }

    userSessionCopy.textContent = "当前未登录用户账号。";
    if (topbarUserBadge) {
        topbarUserBadge.classList.add("hidden");
        topbarUserBadge.title = "当前账号";
        topbarUserBadge.setAttribute("aria-label", "当前账号");
    }
    if (topbarUserBadgeName) {
        topbarUserBadgeName.textContent = "--";
    }
    studentNameInput.readOnly = false;
    studentEmailInput.readOnly = false;

    if (wasAuthenticated) {
        studentNameInput.value = "guest";
        studentEmailInput.value = "";
        bookingStudentNameInput.value = "guest";
        bookingEmailInput.value = "";
    }

    applyVisitorProfilePresentation();
    switchConversationHistoryScope(resolveConversationHistoryStorageScope());
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
    if (areDrawersClosed() && !hasVisibleOverlayModal()) {
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
        closeDrawers();
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

async function loadOperationsWorkbench() {
    if (!ensureAdminOnlyAccess({ responseElement: operationsResponse })) {
        return;
    }
    if (!operationsResponse) {
        return;
    }

    const days = operationsWindow?.value || "7";
    setInlineStatus(operationsResponse, `正在加载最近 ${days} 天运营后台...`, "empty");
    renderOperationsLoadingState();

    try {
        const [workbenchResult, workflowReplayResult] = await Promise.allSettled([
            apiRequest(`/operations/workbench?days=${encodeURIComponent(days)}&limit=6`),
            apiRequest("/workflow/replay"),
        ]);
        if (workbenchResult.status !== "fulfilled") {
            throw new Error(workbenchResult.reason?.message || "运营后台加载失败，请稍后重试。");
        }
        const data = workbenchResult.value;
        renderOperationsSummary(data.overview || {});
        renderOperationsQueues(data.overview?.queues || []);
        renderOperationsTasks(data.operational_tasks || []);
        renderOperationsBookings(data.pending_bookings || []);
        renderOperationsStudentProfiles(data.student_profiles || []);
        renderOperationsSatisfaction(data.satisfaction || {});
        renderOperationsKnowledgeGaps(
            data.question_analytics?.knowledge_gap_suggestions || [],
            data.knowledge_gap_drafts || []
        );
        renderOperationsArtifactDrafts(data.artifact_memory_drafts || []);
        renderOperationsEscalations(data.escalations || []);
        renderOperationsFollowUps(data.follow_up_actions || []);
        renderOperationsSuggestions(data.anonymous_suggestions || []);
        if (workflowReplayResult.status === "fulfilled") {
            renderOperationsWorkflowReplay(workflowReplayResult.value || {});
        } else {
            renderOperationsWorkflowReplayError(
                workflowReplayResult.reason?.message || "Workflow replay 拉取失败。"
            );
        }
        setInlineStatus(operationsResponse, `已加载最近 ${days} 天运营后台。`, "success");
    } catch (error) {
        renderOperationsErrorState(error.message);
        setInlineStatus(operationsResponse, error.message, "error");
    }
}

function renderOperationsLoadingState() {
    const loadingCard = '<div class="list-card"><p class="list-body">正在加载运营数据...</p></div>';
    if (operationsSummary) {
        operationsSummary.innerHTML = "";
    }
    if (operationsWorkflowReplaySummary) {
        operationsWorkflowReplaySummary.innerHTML = "";
    }
    if (operationsWorkflowReplayList) {
        operationsWorkflowReplayList.innerHTML = loadingCard;
    }
    if (operationsQueues) {
        operationsQueues.innerHTML = loadingCard;
    }
    [operationsTasks, operationsBookings, operationsStudentProfiles, operationsSatisfaction, operationsGaps, operationsArtifactDrafts, operationsEscalations, operationsFollowUps, operationsSuggestions].forEach((element) => {
        if (element) {
            element.innerHTML = loadingCard;
        }
    });
}

function renderOperationsErrorState(message) {
    const errorCard = `<div class="list-card"><p class="list-body">${escapeHtml(message)}</p></div>`;
    if (operationsWorkflowReplaySummary) {
        operationsWorkflowReplaySummary.innerHTML = "";
    }
    if (operationsWorkflowReplayList) {
        operationsWorkflowReplayList.innerHTML = errorCard;
    }
    [operationsQueues, operationsTasks, operationsBookings, operationsStudentProfiles, operationsSatisfaction, operationsGaps, operationsArtifactDrafts, operationsEscalations, operationsFollowUps, operationsSuggestions].forEach((element) => {
        if (element) {
            element.innerHTML = errorCard;
        }
    });
}

function renderOperationsWorkflowReplay(report) {
    if (!operationsWorkflowReplaySummary || !operationsWorkflowReplayList) {
        return;
    }
    const totalScenarios = Number(report.total_scenarios || 0);
    const passedScenarios = Number(report.passed_scenarios || 0);
    const failedScenarios = Number(report.failed_scenarios || 0);
    const passRate = totalScenarios > 0 ? `${Math.round((passedScenarios / totalScenarios) * 100)}%` : "0%";
    operationsWorkflowReplaySummary.innerHTML = [
        `规划器 ${escapeHtml(String(report.planner_version || "--"))}`,
        `策略 ${escapeHtml(String(report.policy_version || "--"))}`,
        `场景 ${escapeHtml(String(totalScenarios))}`,
        `通过 ${escapeHtml(String(passedScenarios))}`,
        `失败 ${escapeHtml(String(failedScenarios))}`,
        `通过率 ${escapeHtml(passRate)}`,
    ]
        .map((entry) => `<span class="memory-profile-chip">${entry}</span>`)
        .join("");

    const results = Array.isArray(report.results) ? report.results : [];
    if (!results.length) {
        operationsWorkflowReplayList.innerHTML = '<div class="list-card"><p class="list-body">当前没有 workflow replay 场景结果。</p></div>';
        return;
    }

    const failedResults = results.filter((item) => !item?.passed);
    const displayResults = (failedResults.length ? failedResults : results).slice(0, 6);
    operationsWorkflowReplayList.innerHTML = displayResults
        .map((item) => {
            const stepIds = Array.isArray(item.step_ids) ? item.step_ids : [];
            const stepChips = stepIds.length
                ? `<div class="operations-workflow-steps">${stepIds
                    .slice(0, 8)
                    .map((stepId) => `<span class="operations-workflow-step-chip">${escapeHtml(stepId)}</span>`)
                    .join("")}</div>`
                : "";
            const errors = Array.isArray(item.errors) ? item.errors : [];
            const statusClass = item.passed ? "status-badge-confirmed" : "status-badge-rejected";
            const statusLabel = item.passed ? "通过" : "失败";
            return `
                <article class="list-card list-card-analytics">
                    <h3>${escapeHtml(item.title || item.scenario_id || "未命名场景")}</h3>
                    <p class="list-meta">${escapeHtml(item.scenario_id || "unknown")} | 目标 ${escapeHtml(item.goal || "--")}</p>
                    <p class="list-body">fallback: ${escapeHtml(item.fallback_template || "--")} | 接受执行: ${item.accepted ? "是" : "否"}</p>
                    ${errors.length ? `<p class="list-body analytics-secondary-copy">${escapeHtml(errors[0])}</p>` : ""}
                    ${stepChips}
                    <div class="list-card-actions">
                        <span class="status-badge ${statusClass}">${statusLabel}</span>
                    </div>
                </article>
            `;
        })
        .join("");
}

function renderOperationsWorkflowReplayError(message) {
    if (!operationsWorkflowReplaySummary || !operationsWorkflowReplayList) {
        return;
    }
    operationsWorkflowReplaySummary.innerHTML = "";
    operationsWorkflowReplayList.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(message)}</p></div>`;
}

function renderOperationsSummary(overview) {
    if (!operationsSummary) {
        return;
    }
    const totals = overview.totals || {};
    const analytics = overview.question_analytics || {};
    const neuromem = overview.neuromem || {};
    const plannerMetrics = overview.planner_metrics || {};
    const conversationStats = neuromem.conversation_stats || {};
    const telemetry = conversationStats.telemetry || {};
    const entries = [
        ["知识条目", totals.knowledge_documents || 0],
        ["学生记忆", totals.memory_profiles || 0],
        ["材料草稿", totals.artifact_memory_drafts || 0],
        ["记忆检索", telemetry.query_count || 0],
        ["记忆写回", telemetry.write_count || 0],
        ["记忆遥测", telemetry.event_count || 0],
        ["反馈记录", totals.feedback_records || 0],
        ["规划请求", totals.planner_requests || plannerMetrics.deterministic_total || 0],
        ["规划回退", totals.planner_fallbacks || plannerMetrics.deterministic_fallbacks || 0],
        ["规划分歧", totals.planner_shadow_drifts || 0],
        ["影子错误", totals.planner_shadow_errors || plannerMetrics.shadow_errors || 0],
        ["匿名留言", totals.suggestions || 0],
        ["总问答", analytics.total_exchanges || 0],
        ["人工接管", analytics.human_handoff_count || 0],
    ];
    operationsSummary.innerHTML = entries
        .map(
            ([label, value]) => `
                <article class="operations-metric-card">
                    <span>${escapeHtml(label)}</span>
                    <strong>${escapeHtml(String(value))}</strong>
                </article>
            `
        )
        .join("");
}

function renderOperationsQueues(queues) {
    if (!operationsQueues) {
        return;
    }
    if (!Array.isArray(queues) || !queues.length) {
        operationsQueues.innerHTML = '<div class="list-card"><p class="list-body">当前没有运营队列数据。</p></div>';
        return;
    }
    operationsQueues.innerHTML = queues
        .map(
            (queue) => `
                <article class="operations-queue-card">
                    <div>
                        <span class="operations-queue-label">${escapeHtml(formatOperationQueueLabel(queue.queue_key))}</span>
                        <h3>${escapeHtml(queue.title)}</h3>
                    </div>
                    <strong>${escapeHtml(String(queue.open_count || 0))}</strong>
                    <p>${escapeHtml(String(queue.total_count || 0))} 条总记录</p>
                    <button type="button" class="ghost-button inline-action-button" data-operation-target="${escapeHtml(queue.queue_key)}">查看</button>
                </article>
            `
        )
        .join("");
}

function renderOperationsTasks(tasks) {
    if (!operationsTasks) {
        return;
    }
    if (!Array.isArray(tasks) || !tasks.length) {
        renderOperationsEmpty(operationsTasks, "当前没有待处理运营任务。");
        return;
    }
    operationsTasks.innerHTML = tasks
        .map(
            (task) => `
                <article class="list-card list-card-operations-task operations-task-${escapeHtml(task.operations_status)}">
                    <h3>${escapeHtml(task.title)}</h3>
                    <p class="list-meta">${escapeHtml(formatOperationsTaskType(task.task_type))} | 优先级 ${escapeHtml(String(task.priority || 0))}</p>
                    <p class="list-body">${escapeHtml(task.detail)}</p>
                    <div class="operations-task-meta">
                        ${task.student_name ? `<span>${escapeHtml(task.student_name)}${task.student_email ? ` | ${escapeHtml(task.student_email)}` : ""}</span>` : ""}
                        ${task.assigned_to ? `<span>负责人：${escapeHtml(task.assigned_to)}</span>` : ""}
                        ${task.note ? `<span>备注：${escapeHtml(task.note)}</span>` : ""}
                        ${task.due_at ? `<span>截止：${escapeHtml(formatDateTime(task.due_at))}</span>` : ""}
                    </div>
                    <div class="list-card-actions">
                        <span class="status-badge ${formatOperationsTaskStatusClass(task.operations_status)}">${escapeHtml(formatOperationsTaskStatus(task.operations_status))}</span>
                        <div class="inline-action-group">
                            <button type="button" class="ghost-button inline-action-button" data-operation-task-status="in_progress" data-operation-task-key="${escapeHtml(task.task_key)}">接手</button>
                            <button type="button" class="ghost-button inline-action-button" data-operation-task-status="deferred" data-operation-task-key="${escapeHtml(task.task_key)}">暂缓</button>
                            <button type="button" class="primary-button inline-action-button" data-operation-task-status="done" data-operation-task-key="${escapeHtml(task.task_key)}">完成</button>
                        </div>
                    </div>
                </article>
            `
        )
        .join("");
}

async function handleOperationsTaskAction(event) {
    const button = event.target.closest("[data-operation-task-key]");
    if (!button) {
        return;
    }
    const taskKey = button.dataset.operationTaskKey;
    const status = button.dataset.operationTaskStatus;
    const note = status === "done" ? "已在运营后台标记完成。" : status === "deferred" ? "已暂缓处理。" : "已接手处理。";
    button.disabled = true;
    try {
        await apiRequest(`/operations/tasks/${encodeURIComponent(taskKey)}`, {
            method: "PATCH",
            body: JSON.stringify({ status, assigned_to: "管理员", note }),
        });
        await loadOperationsWorkbench();
    } catch (error) {
        setInlineStatus(operationsResponse, error.message, "error");
    } finally {
        button.disabled = false;
    }
}

function renderOperationsBookings(bookings) {
    if (!operationsBookings) {
        return;
    }
    if (!Array.isArray(bookings) || !bookings.length) {
        renderOperationsEmpty(operationsBookings, "当前没有待审核预约。");
        return;
    }
    operationsBookings.innerHTML = bookings
        .map(
            (booking) => `
                <article class="list-card list-card-booking list-card-booking-pending">
                    <h3>${escapeHtml(booking.topic)}</h3>
                    <p class="list-meta">${escapeHtml(booking.student_name)} | ${escapeHtml(booking.student_email)}</p>
                    <p class="list-body">${escapeHtml(formatBookingWindow(booking.start_at, booking.end_at))}</p>
                    <div class="list-card-actions">
                        <span class="status-badge status-badge-pending">${escapeHtml(booking.status)}</span>
                    </div>
                </article>
            `
        )
        .join("");
}

function renderOperationsStudentProfiles(profiles) {
    if (!operationsStudentProfiles) {
        return;
    }
    if (!Array.isArray(profiles) || !profiles.length) {
        renderOperationsEmpty(operationsStudentProfiles, "当前没有可运营的学生画像。");
        return;
    }
    operationsStudentProfiles.innerHTML = profiles
        .map((profile) => {
            const summaries = (profile.key_summaries || [])
                .slice(0, 2)
                .map((summary) => `<li>${escapeHtml(formatProfileCategoryLabel(summary.category))}：${escapeHtml(summary.summary)}</li>`)
                .join("");
            const recentQuestions = (profile.recent_questions || [])
                .slice(0, 2)
                .map((question) => `<li>${escapeHtml(question)}</li>`)
                .join("");
            return `
                <article class="list-card list-card-memory list-card-operations-profile">
                    <h3>${escapeHtml(profile.student_name)}</h3>
                    <p class="list-meta">${escapeHtml(profile.student_email || profile.student_key)} | ${escapeHtml(profile.segment)}</p>
                    ${summaries ? `<ul class="operations-profile-list">${summaries}</ul>` : ""}
                    ${recentQuestions ? `<p class="list-meta">近期问题</p><ul class="operations-profile-list">${recentQuestions}</ul>` : ""}
                    <p class="list-body analytics-secondary-copy">建议：${escapeHtml(profile.suggested_next_action)}</p>
                    <div class="list-card-actions">
                        <span class="status-badge status-badge-info">画像 ${escapeHtml(String(profile.profile_count || 0))}</span>
                        <span class="status-badge">交互 ${escapeHtml(String(profile.interaction_count || 0))}</span>
                    </div>
                </article>
            `;
        })
        .join("");
}

function renderOperationsSatisfaction(summary) {
    if (!operationsSatisfaction) {
        return;
    }
    const feedbackCount = summary.feedback_count || 0;
    if (!feedbackCount) {
        renderOperationsEmpty(operationsSatisfaction, "当前窗口内还没有反馈数据。");
        return;
    }
    const reasonHtml = (summary.reason_summaries || [])
        .slice(0, 3)
        .map(
            (reason) => `
                <li>
                    <strong>${escapeHtml(reason.reason_label)}</strong>
                    <span>${escapeHtml(String(reason.count || 0))} 条 · ${escapeHtml(formatRate(reason.share || 0))}</span>
                    ${(reason.sample_issues || []).length ? `<small>${escapeHtml(reason.sample_issues[0])}</small>` : ""}
                </li>
            `
        )
        .join("");
    const trendHtml = (summary.trend || [])
        .slice(-5)
        .map(
            (point) => `
                <span class="operations-trend-chip">
                    ${escapeHtml(point.date)} · 好评 ${escapeHtml(formatRate(point.positive_rate || 0))}
                </span>
            `
        )
        .join("");

    operationsSatisfaction.innerHTML = `
        <article class="list-card list-card-satisfaction">
            <div class="operations-satisfaction-grid">
                <span><strong>${escapeHtml(formatRate(summary.positive_rate || 0))}</strong><small>正向率</small></span>
                <span><strong>${escapeHtml(formatRate(summary.unresolved_rate || 0))}</strong><small>未解决</small></span>
                <span><strong>${escapeHtml(formatRate(summary.feedback_coverage_rate || 0))}</strong><small>覆盖率</small></span>
            </div>
            <p class="list-meta">反馈 ${escapeHtml(String(feedbackCount))} 条 | 点踩 ${escapeHtml(String(summary.negative_count || 0))} 条 | 转人工 ${escapeHtml(formatRate(summary.human_handoff_rate || 0))}</p>
            ${reasonHtml ? `<ul class="operations-satisfaction-reasons">${reasonHtml}</ul>` : '<p class="list-body analytics-secondary-copy">暂时没有负面原因。</p>'}
            ${trendHtml ? `<div class="operations-trend-row">${trendHtml}</div>` : ""}
        </article>
    `;
}

function renderOperationsKnowledgeGaps(gaps, drafts) {
    if (!operationsGaps) {
        return;
    }
    const gapItems = Array.isArray(gaps) ? gaps : [];
    const draftItems = Array.isArray(drafts) ? drafts : [];
    if (!gapItems.length && !draftItems.length) {
        renderOperationsEmpty(operationsGaps, "当前没有知识缺口建议或待补草稿。");
        return;
    }

    const gapHtml = gapItems
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

    const draftHtml = draftItems
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

    operationsGaps.innerHTML = [
        gapHtml,
        draftHtml ? `<div class="operations-subsection-title">待补知识草稿</div>${draftHtml}` : "",
    ].filter(Boolean).join("");
}

function renderOperationsArtifactDrafts(drafts) {
    if (!operationsArtifactDrafts) {
        return;
    }
    if (!Array.isArray(drafts) || !drafts.length) {
        renderOperationsEmpty(operationsArtifactDrafts, "当前没有待审核材料草稿。");
        return;
    }
    operationsArtifactDrafts.innerHTML = drafts
        .map(
            (draft) => `
                <article class="list-card list-card-analytics list-card-analytics-draft">
                    <h3>${escapeHtml((draft.artifact_names || []).join("、") || "未命名材料")}</h3>
                    <p class="list-meta">${escapeHtml(draft.student_name)}${draft.student_email ? ` | ${escapeHtml(draft.student_email)}` : ""}</p>
                    <p class="list-body">${escapeHtml(draft.provenance_note)}</p>
                    <p class="list-body analytics-secondary-copy">保留策略：${escapeHtml(draft.retention_label)} | 摘录 ${escapeHtml(String(draft.artifact_excerpt_count || 0))} 条</p>
                    <div class="list-card-actions">
                        <div class="inline-action-group">
                            ${draft.status === "draft"
                    ? `<button type="button" class="ghost-button inline-action-button" data-artifact-draft-reject="${escapeHtml(draft.draft_id)}">驳回</button>
                               <button type="button" class="primary-button inline-action-button" data-artifact-draft-accept="${escapeHtml(draft.draft_id)}">采纳</button>`
                    : ""}
                        </div>
                        <span class="status-badge ${formatArtifactDraftStatusClass(draft.status)}">${escapeHtml(formatArtifactDraftStatusLabel(draft.status))}</span>
                        <span class="list-meta">${escapeHtml(formatDateTime(draft.updated_at))}</span>
                    </div>
                </article>
            `
        )
        .join("");
}

function formatArtifactDraftStatusLabel(status) {
    switch (status) {
        case "accepted":
            return "已采纳";
        case "rejected":
            return "已驳回";
        default:
            return "待审核";
    }
}

function formatArtifactDraftStatusClass(status) {
    switch (status) {
        case "accepted":
            return "status-badge-confirmed";
        case "rejected":
            return "status-badge-rejected";
        default:
            return "status-badge-pending";
    }
}

async function handleArtifactDraftAction(event) {
    if (!ensureAdminOnlyAccess({ responseElement: operationsResponse })) {
        return;
    }
    const acceptButton = event.target.closest("[data-artifact-draft-accept]");
    const rejectButton = event.target.closest("[data-artifact-draft-reject]");
    if (!acceptButton && !rejectButton) {
        return;
    }
    const button = acceptButton || rejectButton;
    const draftId = acceptButton?.dataset.artifactDraftAccept || rejectButton?.dataset.artifactDraftReject;
    const action = acceptButton ? "accept" : "reject";
    button.disabled = true;
    setInlineStatus(operationsResponse, action === "accept" ? "正在采纳材料草稿..." : "正在驳回材料草稿...", "empty");
    try {
        await apiRequest(`/memory/artifact-drafts/${encodeURIComponent(draftId)}/${action}`, {
            method: "POST",
        });
        setInlineStatus(operationsResponse, action === "accept" ? "材料草稿已采纳。" : "材料草稿已驳回。", "success");
        await loadOperationsWorkbench();
    } catch (error) {
        setInlineStatus(operationsResponse, error.message, "error");
    } finally {
        button.disabled = false;
    }
}

function renderOperationsEscalations(records) {
    if (!operationsEscalations) {
        return;
    }
    if (!Array.isArray(records) || !records.length) {
        renderOperationsEmpty(operationsEscalations, "当前没有待处理人工请求。");
        return;
    }
    operationsEscalations.innerHTML = records
        .map(
            (record) => `
                <article class="list-card list-card-escalation list-card-escalation-pending">
                    <h3>${escapeHtml(formatEscalationRouteLabel(record.route))}</h3>
                    <p class="list-meta">${escapeHtml(record.student_name)} | ${escapeHtml(record.student_email || "未提供邮箱")}</p>
                    <p class="list-body">${escapeHtml(record.question)}</p>
                    <div class="list-card-actions">
                        <span class="status-badge status-badge-handoff">${escapeHtml(record.status)}</span>
                    </div>
                </article>
            `
        )
        .join("");
}

function renderOperationsFollowUps(actions) {
    if (!operationsFollowUps) {
        return;
    }
    if (!Array.isArray(actions) || !actions.length) {
        renderOperationsEmpty(operationsFollowUps, "当前没有待发送后续动作。");
        return;
    }
    operationsFollowUps.innerHTML = actions
        .map(
            (action) => `
                <article class="list-card list-card-analytics list-card-analytics-handoff">
                    <h3>${escapeHtml(action.title)}</h3>
                    <p class="list-meta">${escapeHtml(action.student_name)} | ${escapeHtml(action.student_email)}</p>
                    <p class="list-body">${escapeHtml(action.detail)}</p>
                    <div class="list-card-actions">
                        <span class="status-badge status-badge-info">${escapeHtml(formatFollowUpActionLabel(action.action_type))}</span>
                        <span class="list-meta">${escapeHtml(action.due_at ? formatDateTime(action.due_at) : "无截止时间")}</span>
                    </div>
                </article>
            `
        )
        .join("");
}

function renderOperationsSuggestions(records) {
    if (!operationsSuggestions) {
        return;
    }
    if (!Array.isArray(records) || !records.length) {
        renderOperationsEmpty(operationsSuggestions, "当前没有匿名留言。");
        return;
    }
    operationsSuggestions.innerHTML = records
        .map(
            (record) => `
                <article class="list-card list-card-suggestion">
                    <h3>${escapeHtml(record.category || "匿名留言")}</h3>
                    <p class="list-meta">${escapeHtml(formatDateTime(record.created_at))}</p>
                    <p class="list-body">${escapeHtml(record.message)}</p>
                </article>
            `
        )
        .join("");
}

function renderOperationsEmpty(element, message) {
    element.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(message)}</p></div>`;
}

async function handleOperationsQueueAction(event) {
    const button = event.target.closest("[data-operation-target]");
    if (!button) {
        return;
    }
    const target = button.dataset.operationTarget;
    closeModals();
    if (target === "booking_review") {
        openModal(bookingAdminModal);
        await loadBookingList();
    } else if (target === "artifact_memory_drafts") {
        openModal(operationsConsoleModal);
        operationsArtifactDrafts?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (target === "knowledge_gap_drafts") {
        openModal(questionAnalyticsModal);
        await loadQuestionAnalytics();
    } else if (target === "human_handoff") {
        openModal(escalationAdminModal);
        await loadEscalationList();
    } else if (target === "follow_ups") {
        openModal(questionAnalyticsModal);
        await loadQuestionAnalytics();
    } else if (target === "anonymous_suggestions") {
        openModal(suggestionModal);
        await loadSuggestionList();
    }
}

function formatOperationQueueLabel(queueKey) {
    switch (queueKey) {
        case "booking_review":
            return "Booking";
        case "artifact_memory_drafts":
            return "Artifacts";
        case "knowledge_gap_drafts":
            return "Knowledge";
        case "human_handoff":
            return "Handoff";
        case "follow_ups":
            return "Follow-up";
        case "anonymous_suggestions":
            return "Feedback";
        default:
            return "Queue";
    }
}

function formatOperationsTaskType(taskType) {
    switch (taskType) {
        case "booking_review":
            return "预约审核";
        case "artifact_memory_draft":
            return "材料草稿";
        case "knowledge_gap_draft":
            return "知识缺口";
        case "human_handoff":
            return "人工接管";
        case "follow_up":
            return "后续动作";
        case "anonymous_suggestion":
            return "匿名留言";
        case "planner_comparison":
            return "规划分歧";
        default:
            return "运营任务";
    }
}

function formatOperationsTaskStatus(status) {
    switch (status) {
        case "in_progress":
            return "处理中";
        case "done":
            return "已完成";
        case "deferred":
            return "已暂缓";
        default:
            return "待处理";
    }
}

function formatOperationsTaskStatusClass(status) {
    switch (status) {
        case "in_progress":
            return "status-badge-info";
        case "done":
            return "status-badge-confirmed";
        case "deferred":
            return "status-badge-pending";
        default:
            return "status-badge-handoff";
    }
}

function formatRate(value) {
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) {
        return "0%";
    }
    return `${Math.round(numericValue * 100)}%`;
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
    const isOperationsSource = Boolean(operationsGaps && operationsGaps.contains(event.target));
    const responseElement = isOperationsSource ? operationsResponse : questionAnalyticsResponse;
    const days = Number(isOperationsSource ? operationsWindow?.value || 7 : questionAnalyticsWindow?.value || 7);
    if (!ensureAdminOnlyAccess({ responseElement })) {
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
            setInlineStatus(responseElement, "正在生成知识草稿...", "empty");
            await apiRequest("/analytics/questions/gap-drafts", {
                method: "POST",
                body: JSON.stringify({ cluster_id: clusterId, days }),
            });
            setInlineStatus(responseElement, "知识草稿已生成，可继续发布到知识库。", "success");
            await (isOperationsSource ? loadOperationsWorkbench() : loadQuestionAnalytics());
            return;
        }

        if (publishButton) {
            const draftId = publishButton.dataset.gapDraftPublish;
            publishButton.disabled = true;
            setInlineStatus(responseElement, "正在发布知识草稿到知识库...", "empty");
            await apiRequest(`/analytics/questions/gap-drafts/${encodeURIComponent(draftId)}/publish`, {
                method: "POST",
            });
            setInlineStatus(responseElement, "知识草稿已发布到知识库。", "success");
            await refreshStatus();
            await (isOperationsSource ? loadOperationsWorkbench() : loadQuestionAnalytics());
        }
    } catch (error) {
        setInlineStatus(responseElement, error.message, "error");
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

async function loadSuggestionList() {
    if (!suggestionList || !suggestionResponse) {
        return;
    }
    setInlineStatus(suggestionResponse, "正在加载匿名留言...", "empty");
    suggestionList.innerHTML = `<div class="list-card"><p class="list-body">正在加载匿名留言...</p></div>`;

    try {
        const records = await apiRequest("/suggestions?limit=50");
        suggestionList.innerHTML = "";
        if (!records.length) {
            suggestionList.innerHTML = `<div class="list-card"><p class="list-body">目前还没有匿名留言。</p></div>`;
            setInlineStatus(suggestionResponse, "目前还没有匿名留言。", "empty");
            return;
        }

        records.forEach((record) => {
            const card = document.createElement("article");
            card.className = "list-card list-card-suggestion";
            const categoryHtml = record.category
                ? `<span class="status-badge status-badge-info">${escapeHtml(record.category)}</span>`
                : "";
            card.innerHTML = `
                <h3>匿名留言</h3>
                <p class="list-meta">${escapeHtml(formatDateTime(record.created_at))}</p>
                <p class="list-body">${escapeHtml(record.message)}</p>
                <div class="list-card-actions">
                    <div class="inline-action-group">
                        ${categoryHtml}
                    </div>
                </div>
            `;
            suggestionList.appendChild(card);
        });
        setInlineStatus(suggestionResponse, `共有 ${records.length} 条匿名留言。`, "success");
    } catch (error) {
        suggestionList.innerHTML = `<div class="list-card"><p class="list-body">${escapeHtml(error.message)}</p></div>`;
        setInlineStatus(suggestionResponse, error.message, "error");
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
    const requestHeaders = new Headers(fetchOptions.headers || {});
    if (!(fetchOptions.body instanceof FormData) && !requestHeaders.has("Content-Type")) {
        requestHeaders.set("Content-Type", "application/json");
    }

    let response;
    try {
        response = await fetch(requestUrl, {
            headers: requestHeaders,
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
        const friendly = friendlyHttpErrorMessage(response.status, text);
        const error = new Error(friendly);
        error.status = response.status;
        error.responseBody = text;
        throw error;
    }

    return response.json();
}

function friendlyHttpErrorMessage(status, body) {
    const trimmed = typeof body === "string" ? body.trim() : "";
    const looksLikeHtml = trimmed.startsWith("<");
    const detail = looksLikeHtml || trimmed.length > 240 ? "" : trimmed;
    if (status === 413) {
        return "附件超过服务允许的大小。单份附件请控制在 5MB 以内；如果是长 PDF，可以先发主要章节或转成文本后再上传。";
    }
    if (status === 504 || status === 502) {
        return "服务在 LLM 响应期间超时（错误码 " + status + "）。请稍后重试；如果问题较复杂，可以拆成更小的问题再问。";
    }
    if (status === 503) {
        return "后端临时不可用（503），请稍后重试。";
    }
    if (status === 401 || status === 403) {
        return detail || `请求被拒绝（${status}），请重新登录后重试。`;
    }
    if (status >= 500) {
        return detail
            ? `服务内部错误（${status}）：${detail}`
            : `服务内部错误（${status}），请稍后重试。`;
    }
    if (detail) {
        return `请求失败（${status}）：${detail}`;
    }
    return `请求失败（${status}）。`;
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
    const attachmentsHtml = Array.isArray(options.attachments) && options.attachments.length
        ? `
            <div class="message-attachment-row">
                ${options.attachments
            .map((attachment) => `
                    <span class="attachment-chip attachment-chip-readonly">
                        <span class="attachment-chip-copy">
                            <strong>${escapeHtml(attachment.fileName || attachment.file_name || "附件")}</strong>
                            <small>${escapeHtml(formatAttachmentSize(attachment.sizeBytes || attachment.size_bytes || 0))}</small>
                        </span>
                    </span>
                `)
            .join("")}
            </div>
        `
        : "";
    const avatarLabel = role === "user" ? "你" : "S";
    article.className = `message message-${role}${stateClass}${emphasisClass}`;
    article.innerHTML = `
    <div class="message-bubble-row">
        <div class="message-avatar" aria-hidden="true">${avatarLabel}</div>
        <div class="message-bubble">
            <div class="message-role">${escapeHtml(label)}</div>
            <div class="message-frame">
                ${attachmentsHtml}
                <div class="message-body">${formatMessageContent(text)}</div>
            </div>
        </div>
    </div>
  `;
    chatStream.appendChild(article);
    syncConversationMode();
    chatStream.scrollTop = chatStream.scrollHeight;
    return article;
}

function resolveConversationHistoryStorageScope() {
    const email = getCurrentHistorySyncEmail();
    return email ? `user:${email}` : "guest";
}

function buildConversationHistoryStorageKey(scope = conversationHistoryScope) {
    return `${CHAT_HISTORY_STORAGE_KEY}:${scope || "guest"}`;
}

function buildConversationHistoryMetaStorageKey(scope = conversationHistoryScope) {
    return `${CHAT_HISTORY_META_STORAGE_KEY}:${scope || "guest"}`;
}

function loadConversationHistory(scope = conversationHistoryScope) {
    try {
        const raw = globalThis.localStorage?.getItem(buildConversationHistoryStorageKey(scope));
        if (!raw) {
            return [];
        }
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed)) {
            return [];
        }
        return parsed
            .map((entry) => ({
                id: typeof entry?.id === "string" ? entry.id : "",
                title: typeof entry?.title === "string" ? entry.title : DEFAULT_CONVERSATION_TITLE,
                preview: typeof entry?.preview === "string" ? entry.preview : "",
                html: typeof entry?.html === "string" ? entry.html : "",
                updatedAt: Number.isFinite(entry?.updatedAt) ? entry.updatedAt : Date.now(),
                exchangeCount: Number.isFinite(entry?.exchangeCount) ? entry.exchangeCount : 1,
                source: "local",
            }))
            .filter((entry) => entry.id && entry.html)
            .sort((left, right) => right.updatedAt - left.updatedAt)
            .slice(0, MAX_CHAT_HISTORY_ITEMS);
    } catch {
        return [];
    }
}

function loadConversationHistoryMeta(scope = conversationHistoryScope) {
    try {
        const raw = globalThis.localStorage?.getItem(buildConversationHistoryMetaStorageKey(scope));
        if (!raw) {
            return { titleOverrides: {}, hiddenIds: [] };
        }
        const parsed = JSON.parse(raw);
        const titleOverrides = parsed?.titleOverrides && typeof parsed.titleOverrides === "object"
            ? Object.fromEntries(
                Object.entries(parsed.titleOverrides)
                    .filter(([key, value]) => typeof key === "string" && typeof value === "string" && value.trim())
            )
            : {};
        const hiddenIds = Array.isArray(parsed?.hiddenIds)
            ? parsed.hiddenIds.filter((value) => typeof value === "string" && value.trim())
            : [];
        return { titleOverrides, hiddenIds };
    } catch {
        return { titleOverrides: {}, hiddenIds: [] };
    }
}

function saveConversationHistory() {
    try {
        globalThis.localStorage?.setItem(
            buildConversationHistoryStorageKey(),
            JSON.stringify(conversationHistoryEntries.slice(0, MAX_CHAT_HISTORY_ITEMS))
        );
    } catch {
        // Ignore persistence failures in privacy-restricted modes.
    }
}

function saveConversationHistoryMeta() {
    try {
        globalThis.localStorage?.setItem(
            buildConversationHistoryMetaStorageKey(),
            JSON.stringify(conversationHistoryMeta)
        );
    } catch {
        // Ignore persistence failures in privacy-restricted modes.
    }
}

function buildConversationTitle(text) {
    const normalized = String(text || "").replace(/\s+/g, " ").trim();
    if (!normalized) {
        return DEFAULT_CONVERSATION_TITLE;
    }
    return normalized.length > 20 ? `${normalized.slice(0, 20)}...` : normalized;
}

function buildConversationPreview(text) {
    const normalized = String(text || "").replace(/\s+/g, " ").trim();
    if (!normalized) {
        return "";
    }
    return normalized.length > 48 ? `${normalized.slice(0, 48)}...` : normalized;
}

function noteOutgoingConversationQuestion(question) {
    if (!currentConversationTitle || currentConversationTitle === DEFAULT_CONVERSATION_TITLE) {
        currentConversationTitle = buildConversationTitle(question);
    }
    currentConversationPreview = buildConversationPreview(question);
}

function noteConversationAnswerPreview(answerText) {
    const preview = buildConversationPreview(answerText);
    if (preview) {
        currentConversationPreview = preview;
    }
}

function getCurrentHistorySyncEmail() {
    return currentUserAccountEmail || "";
}

function resetConversationViewForHistoryScopeSwitch() {
    stopWorkflowTraceStream();
    activeWorkflowSteps = [];
    activeConversationId = createConversationId();
    currentConversationTitle = DEFAULT_CONVERSATION_TITLE;
    currentConversationPreview = "";
    latestWorkflowMeta = {
        workflowAction: null,
        knowledgeHits: null,
        isStreaming: false,
        plannerPreview: null,
        shadowPlannerPreview: null,
        plannerComparison: null,
    };
    clearPendingChatAttachments();
    if (chatStream) {
        chatStream.innerHTML = initialChatStreamMarkup;
    }
    syncIntroCardPresentation();
    syncConversationMode();
    renderWorkflowTrace([], latestWorkflowMeta);
    chatSubmitButton.disabled = false;
    chatSubmitButton.textContent = "发送";
}

function switchConversationHistoryScope(nextScope, { preserveCurrentSnapshot = true } = {}) {
    const normalizedScope = String(nextScope || "guest").trim() || "guest";
    if (normalizedScope === conversationHistoryScope) {
        return;
    }

    if (preserveCurrentSnapshot && hasRenderableConversation()) {
        persistActiveConversationSnapshot();
    }

    conversationHistoryScope = normalizedScope;
    conversationHistoryEntries = loadConversationHistory(conversationHistoryScope);
    conversationHistoryMeta = loadConversationHistoryMeta(conversationHistoryScope);
    serverConversationEntries = [];
    resetConversationViewForHistoryScopeSwitch();
    renderConversationHistoryList();
}

function buildMergedConversationEntries() {
    const merged = new Map();

    serverConversationEntries.forEach((entry) => {
        merged.set(entry.id, { ...entry, source: "server" });
    });

    conversationHistoryEntries.forEach((entry) => {
        const existing = merged.get(entry.id) || {};
        merged.set(entry.id, {
            ...existing,
            ...entry,
            title: entry.title || existing.title || DEFAULT_CONVERSATION_TITLE,
            preview: entry.preview || existing.preview || "",
            updatedAt: Math.max(Number(existing.updatedAt || 0), Number(entry.updatedAt || 0)),
            exchangeCount: Math.max(Number(existing.exchangeCount || 1), Number(entry.exchangeCount || 1)),
            source: existing.id ? "hybrid" : "local",
        });
    });

    return [...merged.values()]
        .filter((entry) => !conversationHistoryMeta.hiddenIds.includes(entry.id))
        .map((entry) => ({
            ...entry,
            title: conversationHistoryMeta.titleOverrides[entry.id] || entry.title || DEFAULT_CONVERSATION_TITLE,
            preview: entry.preview || "点击继续这段对话",
        }))
        .sort((left, right) => right.updatedAt - left.updatedAt)
        .slice(0, MAX_CHAT_HISTORY_ITEMS);
}

function groupConversationHistoryEntries(entries) {
    const groups = [
        { key: "today", label: "今天", items: [] },
        { key: "recent", label: "最近 7 天", items: [] },
        { key: "older", label: "更早", items: [] },
    ];
    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const recentThreshold = startOfToday - 6 * 24 * 60 * 60 * 1000;

    entries.forEach((entry) => {
        const timestamp = Number(entry.updatedAt || 0);
        if (timestamp >= startOfToday) {
            groups[0].items.push(entry);
        } else if (timestamp >= recentThreshold) {
            groups[1].items.push(entry);
        } else {
            groups[2].items.push(entry);
        }
    });

    return groups.filter((group) => group.items.length);
}

function hasRenderableConversation() {
    return Boolean(chatStream?.querySelector(".message-user, .message-pending, .message-ready"));
}

function persistActiveConversationSnapshot() {
    if (!chatStream || !hasRenderableConversation()) {
        renderConversationHistoryList();
        return;
    }

    const entry = {
        id: activeConversationId,
        title: conversationHistoryMeta.titleOverrides[activeConversationId] || currentConversationTitle || DEFAULT_CONVERSATION_TITLE,
        preview: currentConversationPreview || buildConversationPreview(chatStream.textContent || ""),
        html: chatStream.innerHTML,
        updatedAt: Date.now(),
        exchangeCount: chatStream.querySelectorAll(".message-user").length || 1,
        source: "local",
    };

    conversationHistoryEntries = [entry, ...conversationHistoryEntries.filter((item) => item.id !== activeConversationId)]
        .slice(0, MAX_CHAT_HISTORY_ITEMS);
    saveConversationHistory();
    renderConversationHistoryList();
}

function renderConversationHistoryList() {
    if (!historyList) {
        return;
    }

    const mergedEntries = buildMergedConversationEntries();

    if (!mergedEntries.length) {
        historyList.innerHTML = `<div class="history-empty">${escapeHtml(getCurrentHistorySyncEmail() ? "还没有可恢复的历史对话。" : "新的对话会出现在这里；登录或填写邮箱后也能同步到其他设备。")}</div>`;
        return;
    }

    historyList.innerHTML = groupConversationHistoryEntries(mergedEntries)
        .map((group) => `
            <section class="history-group" aria-label="${escapeHtml(group.label)}">
                <h3 class="history-group-title">${escapeHtml(group.label)}</h3>
                <div class="history-group-list">
                    ${group.items.map((entry) => {
            const isActive = entry.id === activeConversationId && hasRenderableConversation();
            return `
                            <article class="history-item ${isActive ? "history-item-active" : ""}">
                                <button type="button" class="history-item-main" data-history-id="${escapeHtml(entry.id)}">
                                    <div class="history-item-head">
                                        <strong class="history-item-title">${escapeHtml(entry.title || DEFAULT_CONVERSATION_TITLE)}</strong>
                                        <span class="history-item-time">${escapeHtml(formatConversationHistoryTime(entry.updatedAt))}</span>
                                    </div>
                                    <p class="history-item-preview">${escapeHtml(entry.preview || "点击继续这段对话")}</p>
                                    <div class="history-item-meta-row">
                                        <span class="history-item-badge">${isActive ? "当前" : `${escapeHtml(String(entry.exchangeCount || 1))} 轮`}</span>
                                        ${entry.source === "server" || entry.source === "hybrid" ? '<span class="history-item-sync">已同步</span>' : ""}
                                    </div>
                                </button>
                                <div class="history-item-actions">
                                    <button type="button" class="history-item-action" data-history-rename="${escapeHtml(entry.id)}">改名</button>
                                    <button type="button" class="history-item-action" data-history-remove="${escapeHtml(entry.id)}">移除</button>
                                </div>
                            </article>
                        `;
        }).join("")}
                </div>
            </section>
        `)
        .join("");
}

function formatConversationHistoryTime(timestamp) {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) {
        return "刚刚";
    }

    const now = new Date();
    const sameDay = date.toDateString() === now.toDateString();
    if (sameDay) {
        return new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit" }).format(date);
    }
    return new Intl.DateTimeFormat("zh-CN", { month: "numeric", day: "numeric" }).format(date);
}

async function handleConversationHistoryClick(event) {
    const renameTrigger = event.target.closest("[data-history-rename]");
    if (renameTrigger && historyList?.contains(renameTrigger)) {
        handleConversationRename(renameTrigger.dataset.historyRename || "");
        return;
    }

    const removeTrigger = event.target.closest("[data-history-remove]");
    if (removeTrigger && historyList?.contains(removeTrigger)) {
        handleConversationRemove(removeTrigger.dataset.historyRemove || "");
        return;
    }

    const trigger = event.target.closest("[data-history-id]");
    if (!trigger || !historyList?.contains(trigger)) {
        return;
    }

    const conversationId = trigger.dataset.historyId || "";
    if (!conversationId || conversationId === activeConversationId) {
        return;
    }

    persistActiveConversationSnapshot();
    await restoreConversationFromHistory(conversationId);
    if (isMobileWorkflowViewport()) {
        setHistoryRailCollapsed(true);
    }
}

function handleConversationRename(conversationId) {
    if (!conversationId) {
        return;
    }
    const entry = buildMergedConversationEntries().find((item) => item.id === conversationId);
    if (!entry) {
        return;
    }
    const nextTitle = globalThis.prompt("重命名这段对话", entry.title || DEFAULT_CONVERSATION_TITLE);
    if (nextTitle === null) {
        return;
    }
    const normalized = nextTitle.trim();
    if (!normalized) {
        delete conversationHistoryMeta.titleOverrides[conversationId];
    } else {
        conversationHistoryMeta.titleOverrides[conversationId] = buildConversationTitle(normalized);
    }
    if (conversationId === activeConversationId) {
        currentConversationTitle = conversationHistoryMeta.titleOverrides[conversationId] || currentConversationTitle;
        persistActiveConversationSnapshot();
    }
    saveConversationHistoryMeta();
    renderConversationHistoryList();
}

function handleConversationRemove(conversationId) {
    if (!conversationId) {
        return;
    }
    const confirmed = globalThis.confirm("把这段对话从左栏隐藏？本地快照会移除，服务端同步记录也不会再显示。 ");
    if (!confirmed) {
        return;
    }
    conversationHistoryMeta.hiddenIds = [...new Set([...conversationHistoryMeta.hiddenIds, conversationId])];
    delete conversationHistoryMeta.titleOverrides[conversationId];
    conversationHistoryEntries = conversationHistoryEntries.filter((entry) => entry.id !== conversationId);
    saveConversationHistory();
    saveConversationHistoryMeta();
    if (conversationId === activeConversationId) {
        startFreshConversation();
        return;
    }
    renderConversationHistoryList();
}

async function restoreConversationFromHistory(conversationId) {
    const entry = conversationHistoryEntries.find((item) => item.id === conversationId);
    if (!chatStream) {
        return;
    }

    stopWorkflowTraceStream();
    activeWorkflowSteps = [];
    activeConversationId = conversationId;
    if (entry?.html) {
        currentConversationTitle = conversationHistoryMeta.titleOverrides[conversationId] || entry.title || DEFAULT_CONVERSATION_TITLE;
        currentConversationPreview = entry.preview || "";
        chatStream.innerHTML = entry.html || initialChatStreamMarkup;
        hydrateConversationInteractiveState();
        renderConversationHistoryList();
        renderWorkflowTrace([], {
            workflowAction: null,
            knowledgeHits: null,
            isStreaming: false,
            currentLabel: undefined,
            plannerPreview: null,
            shadowPlannerPreview: null,
            plannerComparison: null,
        });
        chatStream.scrollTop = 0;
        return;
    }

    try {
        const transcript = await fetchConversationTranscript(conversationId);
        renderConversationTranscript(transcript);
        renderConversationHistoryList();
    } catch (error) {
        currentConversationTitle = DEFAULT_CONVERSATION_TITLE;
        currentConversationPreview = "";
        startFreshConversation();
        console.error(error);
    }
}

async function fetchConversationTranscript(conversationId) {
    const email = getCurrentHistorySyncEmail();
    if (!email) {
        throw new Error("当前没有可用于同步历史的邮箱信息。");
    }
    return apiRequest(`/chat/conversations/${encodeURIComponent(conversationId)}`, { timeoutMs: 10000 });
}

function renderConversationTranscript(transcript) {
    if (!chatStream || !transcript) {
        return;
    }

    chatStream.innerHTML = "";
    currentConversationTitle = conversationHistoryMeta.titleOverrides[transcript.conversation_id] || transcript.title || DEFAULT_CONVERSATION_TITLE;
    currentConversationPreview = transcript.preview || "";
    activeConversationId = transcript.conversation_id;

    const speakerName = transcript.student_name || studentNameInput?.value || "学生";
    const exchanges = Array.isArray(transcript.exchanges) ? transcript.exchanges : [];
    if (!exchanges.length) {
        chatStream.innerHTML = initialChatStreamMarkup;
        syncIntroCardPresentation();
        syncConversationMode();
        return;
    }

    exchanges.forEach((exchange) => {
        appendMessage("user", speakerName, exchange.question, {});
        appendMessage("assistant", assistantLabel, exchange.answer, {});
    });
    syncConversationMode();
}

async function syncConversationHistoryFromServer() {
    const email = getCurrentHistorySyncEmail();
    if (!email) {
        serverConversationEntries = [];
        renderConversationHistoryList();
        return;
    }

    try {
        const params = new URLSearchParams({ limit: String(MAX_CHAT_HISTORY_ITEMS) });
        const data = await apiRequest(`/chat/conversations?${params.toString()}`, { timeoutMs: 8000 });
        serverConversationEntries = Array.isArray(data?.conversations)
            ? data.conversations.map((entry) => ({
                id: String(entry.conversation_id || ""),
                title: String(entry.title || DEFAULT_CONVERSATION_TITLE),
                preview: String(entry.preview || "点击继续这段对话"),
                updatedAt: Date.parse(String(entry.last_message_at || "")) || Date.now(),
                exchangeCount: Number(entry.exchange_count || 1),
                source: "server",
            })).filter((entry) => entry.id)
            : [];
    } catch {
        serverConversationEntries = [];
    }

    renderConversationHistoryList();
}

function setHistoryRailCollapsed(collapsed) {
    document.body.classList.toggle("history-rail-collapsed", collapsed);
    if (historyRailToggleButton) {
        historyRailToggleButton.textContent = collapsed ? "展开" : "收起";
        historyRailToggleButton.setAttribute("aria-expanded", String(!collapsed));
    }
    if (topbarMobileHistoryToggleButton) {
        topbarMobileHistoryToggleButton.setAttribute("aria-label", collapsed ? "历史对话" : "收起历史");
        topbarMobileHistoryToggleButton.setAttribute("title", collapsed ? "历史对话" : "收起历史");
        topbarMobileHistoryToggleButton.setAttribute("aria-expanded", String(!collapsed));
    }
    if (topbarHistoryToggleButton) {
        topbarHistoryToggleButton.setAttribute("aria-label", collapsed ? "历史对话" : "收起历史");
        topbarHistoryToggleButton.setAttribute("title", collapsed ? "历史对话" : "收起历史");
        topbarHistoryToggleButton.setAttribute("aria-expanded", String(!collapsed));
    }
    try {
        globalThis.localStorage?.setItem(HISTORY_RAIL_COLLAPSED_KEY, collapsed ? "1" : "0");
    } catch {
        // Ignore persistence failures in privacy-restricted modes.
    }
}

function toggleHistoryRail() {
    setHistoryRailCollapsed(!document.body.classList.contains("history-rail-collapsed"));
}

function restoreHistoryRailState() {
    try {
        setHistoryRailCollapsed(globalThis.localStorage?.getItem(HISTORY_RAIL_COLLAPSED_KEY) !== "0");
    } catch {
        setHistoryRailCollapsed(true);
    }
}

function hydrateConversationInteractiveState() {
    syncConversationMode();
    attachFeedbackHandlersToStream();
}

function attachFeedbackHandlersToStream() {
    if (!chatStream) {
        return;
    }
    chatStream.querySelectorAll(".message-feedback[data-feedback-exchange]").forEach((feedbackSection) => {
        const container = feedbackSection.closest(".message");
        const exchangeId = feedbackSection.dataset.feedbackExchange || "";
        if (container && exchangeId) {
            attachFeedbackHandlers(container, exchangeId);
        }
    });
}

function startFreshConversation() {
    if (hasRenderableConversation()) {
        persistActiveConversationSnapshot();
    }

    stopWorkflowTraceStream();
    activeWorkflowSteps = [];
    activeConversationId = createConversationId();
    currentConversationTitle = DEFAULT_CONVERSATION_TITLE;
    currentConversationPreview = "";
    latestWorkflowMeta = {
        workflowAction: null,
        knowledgeHits: null,
        isStreaming: false,
        plannerPreview: null,
        shadowPlannerPreview: null,
        plannerComparison: null,
    };
    clearPendingChatAttachments();
    if (chatStream) {
        chatStream.innerHTML = initialChatStreamMarkup;
    }
    syncIntroCardPresentation();
    renderConversationHistoryList();
    syncConversationMode();
    renderWorkflowTrace([], latestWorkflowMeta);
    chatSubmitButton.disabled = false;
    chatSubmitButton.textContent = "发送";
    chatQuestion?.focus();
}

function syncConversationMode() {
    if (!chatStream) {
        return;
    }
    const hasConversation = Boolean(chatStream.querySelector(".message-user, .message-pending, .message-ready"));
    document.body.classList.toggle("conversation-active", hasConversation);
}

function renderPendingAssistantMessage(container, currentStage = "理解问题", workflowSteps = []) {
    container.innerHTML = `
        <div class="message-bubble-row">
            <div class="message-avatar" aria-hidden="true">S</div>
            <div class="message-bubble">
                <div class="message-role">${escapeHtml(assistantLabel)}</div>
                <div class="message-frame message-pending-frame">
                    <div class="typing-dots" id="pending-typing-dots">
                        <span class="dot"></span>
                        <span class="dot"></span>
                        <span class="dot"></span>
                    </div>
                    <div class="thinking-panel">
                        <div class="thinking-panel-head">
                            <span class="thinking-orb" aria-hidden="true"></span>
                            <div>
                                <strong>正在处理</strong>
                                <p id="pending-stage-label" class="thinking-stage-label">${escapeHtml(currentStage)}</p>
                            </div>
                        </div>
                        <div class="thinking-phase-rail" aria-live="polite">
                            ${buildWorkflowPhaseRailHtml({ currentStage, workflowSteps, complete: false })}
                        </div>
                        <div class="thinking-trace" aria-label="实时处理过程">
                            <div class="thinking-trace-list"></div>
                        </div>
                    </div>
                    <div class="thinking-text-section" id="pending-thinking-text" data-collapsed="false" hidden>
                        <button type="button" class="thinking-text-toggle" onclick="this.parentElement.dataset.collapsed = this.parentElement.dataset.collapsed === 'true' ? 'false' : 'true'">思考过程</button>
                        <div class="thinking-text-body"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    syncPendingWorkflowTrace(workflowSteps, { animateNewItems: false, currentStage });
}

function updatePendingAssistantMessage(currentStage, workflowSteps = []) {
    const pendingLabel = chatStream?.querySelector(".message-pending #pending-stage-label");
    if (pendingLabel) {
        pendingLabel.textContent = currentStage;
    }
    const pendingRail = chatStream?.querySelector(".message-pending .thinking-phase-rail");
    if (pendingRail) {
        pendingRail.innerHTML = buildWorkflowPhaseRailHtml({
            currentStage,
            workflowSteps,
            complete: false,
        });
    }

    syncPendingWorkflowTrace(workflowSteps, { animateNewItems: true, currentStage });
}

function renderAssistantMessage(
    container,
    text,
    basisItems,
    followUpActions,
    hits,
    bookingResult = null,
    isError = false,
    exchangeId = null,
    workflowTrace = []
) {
    const bodyClass = isError ? "message-body" : "message-body";
    const afterNotification = stripNotificationText(text, bookingResult?.notification || null);
    // Strip <think>...</think> from the final answer and optionally display it
    const thinkParsed = parseStreamingThinkContent(afterNotification);
    const cleanedText = thinkParsed.main.trimStart() || (thinkParsed.think ? "" : afterNotification);
    const thinkContent = thinkParsed.think.trim();
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
            countLabel: "需确认",
            sectionClassName: "message-section-follow-up",
            closedLabel: "确认查看",
            openLabel: "收起",
            contentHtml: `
                <div class="message-basis-list">
                    ${followUpActions.map((action) => buildFollowUpActionHtml(action)).join("")}
                </div>
            `,
        })
        : "";
    const workflowTraceHtml = Array.isArray(workflowTrace) && workflowTrace.length
        ? buildWorkflowStatusSummaryHtml(workflowTrace)
        : "";
    const thinkSectionHtml = thinkContent
        ? `<div class="thinking-text-section" data-collapsed="true">
               <button type="button" class="thinking-text-toggle" onclick="this.parentElement.dataset.collapsed = this.parentElement.dataset.collapsed === 'true' ? 'false' : 'true'">思考过程</button>
               <div class="thinking-text-body">${escapeHtml(thinkContent)}</div>
           </div>`
        : "";
    container.innerHTML = `
        <div class="message-bubble-row">
            <div class="message-avatar" aria-hidden="true">S</div>
            <div class="message-bubble">
                <div class="message-role">${escapeHtml(assistantLabel)}</div>
                <div class="message-frame">
                    <div class="message-main-copy">
                        <div class="message-reply-block">
                            <span class="message-section-kicker">Reply</span>
                            <div class="${bodyClass}">${formatMessageContent(cleanedText)}</div>
                            <button type="button" class="message-copy-button" data-copy-answer title="复制回答">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                            </button>
                        </div>
                        ${thinkSectionHtml}
                        ${workflowTraceHtml}
                    </div>
                    ${notificationHtml}
                    ${basisHtml}
                    ${followUpHtml}
                    ${buildFeedbackSectionHtml(exchangeId, isError)}
                </div>
            </div>
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

function buildWorkflowStatusSummaryHtml(workflowTrace) {
    if (!Array.isArray(workflowTrace) || !workflowTrace.length) {
        return "";
    }

    const latestStep = workflowTrace[workflowTrace.length - 1] || null;
    const totalDurationMs = workflowTrace.reduce(
        (sum, step) => (typeof step?.duration_ms === "number" ? sum + step.duration_ms : sum),
        0
    );
    const completedPhaseCount = deriveWorkflowPhaseStates({ workflowSteps: workflowTrace, complete: true })
        .filter((phase) => phase.state === "completed")
        .length;
    const preview = latestStep
        ? `${completedPhaseCount}/${WORKFLOW_PHASE_DEFINITIONS.length} 段 · ${workflowTrace.length} 步 · ${totalDurationMs > 0 ? formatWorkflowDuration(totalDurationMs) : "处理中"}`
        : `${workflowTrace.length} 步`;

    return `
        <section class="message-workflow-summary message-section" data-expanded="false" aria-label="本次处理过程">
            <div class="message-workflow-summary-head">
                <div class="message-workflow-summary-copy">
                    <span class="message-section-kicker">Workflow</span>
                    <strong class="message-section-title">处理进展</strong>
                </div>
                <div class="message-workflow-summary-meta">
                    <span class="message-inline-process-preview">${escapeHtml(preview)}</span>
                </div>
            </div>
            ${buildWorkflowPhaseRailHtml({ workflowSteps: workflowTrace, complete: true })}
            <button type="button" class="message-section-toggle message-workflow-summary-toggle" aria-expanded="false" data-closed-label="展开完整步骤" data-open-label="收起详情">
                <div class="message-section-toggle-copy">
                    <span class="message-workflow-summary-note">默认只显示简化阶段，完整步骤按需展开。</span>
                </div>
                <div class="message-section-toggle-meta">
                    <span class="message-section-count">${escapeHtml(`${workflowTrace.length} 步`)}</span>
                    <span class="message-section-chevron">展开完整步骤</span>
                </div>
            </button>
            <div class="message-section-content" hidden>
                <div class="message-workflow-chip-row">
                    ${buildWorkflowChipRowHtml(workflowTrace)}
                </div>
            </div>
        </section>
    `;
}

function buildWorkflowPhaseRailHtml({ currentStage = "", workflowSteps = [], complete = false } = {}) {
    const phases = deriveWorkflowPhaseStates({ currentStage, workflowSteps, complete });
    return `
        <div class="workflow-phase-rail" aria-label="当前处理阶段">
            ${phases.map((phase, index) => `
                <div class="workflow-phase-item workflow-phase-item-${escapeHtml(phase.state)}" data-phase-key="${escapeHtml(phase.key)}">
                    <span class="workflow-phase-icon" aria-hidden="true">${buildWorkflowPhaseIconSvg(phase.icon)}</span>
                    <span class="workflow-phase-label">${escapeHtml(phase.label)}</span>
                    ${index < phases.length - 1 ? '<span class="workflow-phase-link" aria-hidden="true"></span>' : ""}
                </div>
            `).join("")}
        </div>
    `;
}

function buildWorkflowPhaseIconSvg(iconName) {
    const iconMap = {
        inbox: `
            <svg viewBox="0 0 24 24" fill="none" focusable="false">
                <path d="M4.5 8.4 7.1 5.5h9.8l2.6 2.9v9.1H4.5Z" stroke="currentColor" stroke-width="1.7"/>
                <path d="M8.4 12.3h7.2" stroke="currentColor" stroke-width="1.7"/>
                <path d="m12 8.1 2 2-2 2" stroke="currentColor" stroke-width="1.7"/>
            </svg>`,
        branch: `
            <svg viewBox="0 0 24 24" fill="none" focusable="false">
                <circle cx="7" cy="6.5" r="2.1" stroke="currentColor" stroke-width="1.7"/>
                <circle cx="17" cy="6.5" r="2.1" stroke="currentColor" stroke-width="1.7"/>
                <circle cx="12" cy="17.2" r="2.1" stroke="currentColor" stroke-width="1.7"/>
                <path d="M9 7.6c1.3 1 2.1 2.3 3 5.3M15 7.6c-1.3 1-2.1 2.3-3 5.3" stroke="currentColor" stroke-width="1.7"/>
            </svg>`,
        search: `
            <svg viewBox="0 0 24 24" fill="none" focusable="false">
                <circle cx="10.4" cy="10.4" r="4.6" stroke="currentColor" stroke-width="1.7"/>
                <path d="m14 14 4.1 4.1" stroke="currentColor" stroke-width="1.7"/>
                <path d="M8.3 10.4h4.2" stroke="currentColor" stroke-width="1.7"/>
            </svg>`,
        message: `
            <svg viewBox="0 0 24 24" fill="none" focusable="false">
                <path d="M5 6.6h14v8.5h-7l-3.7 3.3v-3.3H5z" stroke="currentColor" stroke-width="1.7"/>
                <path d="M8.3 10.1h7.2M8.3 12.8h4.8" stroke="currentColor" stroke-width="1.7"/>
                <path d="m16.8 5.1.5 1.3 1.3.5-1.3.5-.5 1.3-.5-1.3-1.3-.5 1.3-.5z" stroke="currentColor" stroke-width="1.4"/>
            </svg>`,
        checklist: `
            <svg viewBox="0 0 24 24" fill="none" focusable="false">
                <rect x="5" y="4.8" width="14" height="14.5" rx="3.2" stroke="currentColor" stroke-width="1.7"/>
                <path d="M9.4 9.1h5.8M9.4 12.3h5.8M9.4 15.5h4.1" stroke="currentColor" stroke-width="1.7"/>
                <path d="m7.2 9.3.7.7 1.3-1.5M7.2 15.7l.7.7 1.3-1.5" stroke="currentColor" stroke-width="1.6"/>
            </svg>`,
        send: `
            <svg viewBox="0 0 24 24" fill="none" focusable="false">
                <path d="M4.8 12 19 5.6l-4.3 12.8-3.1-5.2-6.8-.1Z" stroke="currentColor" stroke-width="1.7"/>
                <path d="M11.7 13 18.8 5.8" stroke="currentColor" stroke-width="1.7"/>
                <path d="M9.5 18.2h5.3" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
            </svg>`,
    };
    return iconMap[iconName] || iconMap.message;
}

function deriveWorkflowPhaseStates({ currentStage = "", workflowSteps = [], complete = false } = {}) {
    const visibleSteps = buildVisibleWorkflowSteps(workflowSteps, currentStage, { includeCurrentStage: !complete });
    const lastVisibleStep = visibleSteps[visibleSteps.length - 1] || null;
    const activePhaseIndex = lastVisibleStep
        ? WORKFLOW_PHASE_DEFINITIONS.findIndex((phase) => phase.key === inferWorkflowPhaseKey(lastVisibleStep))
        : 0;

    return WORKFLOW_PHASE_DEFINITIONS.map((definition, index) => {
        let state = "pending";
        if (complete) {
            state = index <= activePhaseIndex ? "completed" : "pending";
        } else if (index < activePhaseIndex) {
            state = "completed";
        } else if (index === activePhaseIndex) {
            state = "active";
        }
        return {
            ...definition,
            state,
        };
    });
}

function inferWorkflowPhaseKey(step) {
    const key = String(step?.key || "");
    const normalized = `${key} ${String(step?.title || "")}`.toLowerCase();

    if (key === "response_render" || /返回结果|return|response/.test(normalized)) {
        return "return";
    }
    if (
        ["follow_up_plan", "memory_usefulness_score", "memory_persist", "artifact_memory_writeback", "memory_profile_consolidate"].includes(key)
        || /规划后续|评估记忆|写入对话记忆|记录材料|沉淀长期画像|persist|follow_up|usefulness/.test(normalized)
    ) {
        return "finalize";
    }
    if (["prompt_build", "llm_answer"].includes(key) || /构造回答上下文|生成回答|回答|回复|answer|prompt|llm/.test(normalized)) {
        return "answer";
    }
    if (["knowledge_retrieve", "memory_retrieve"].includes(key) || /检索|记忆|资料|上下文|retrieve|memory|knowledge|search/.test(normalized)) {
        return "retrieve";
    }
    if (["workflow_plan_preview", "interaction_understand", "booking_prepare", "booking_execute", "knowledge_write", "current_stage"].includes(key)
        || /预览|理解用户意图|预约|知识入库|当前处理中|plan|intent|booking/.test(normalized)) {
        return "decide";
    }
    return "intake";
}

function buildVisibleWorkflowSteps(workflowSteps = [], currentStage = "", options = {}) {
    const normalizedSteps = Array.isArray(workflowSteps) ? [...workflowSteps] : [];
    const includeCurrentStage = Boolean(options.includeCurrentStage);
    const currentTitle = String(currentStage || "").trim();
    const latestTitle = String(normalizedSteps[normalizedSteps.length - 1]?.title || "").trim();
    if (includeCurrentStage && currentTitle && currentTitle !== latestTitle) {
        normalizedSteps.push({
            key: "current_stage",
            title: currentTitle,
            summary: "当前正在执行这一步。",
            detail: "前面的步骤已经完成，系统正在推进这一环。",
            status: "active",
        });
    }
    return normalizedSteps;
}

function buildCollapsibleSupportSectionHtml({
    kicker,
    title,
    copy,
    count,
    countLabel,
    contentHtml,
    sectionClassName = "message-section-support",
    defaultExpanded = false,
    closedLabel = "查看",
    openLabel = "收起",
}) {
    const resolvedCountLabel = countLabel || (Number.isFinite(count) ? `${count} 条` : closedLabel);
    return `
        <section class="message-section ${escapeHtml(sectionClassName)}" data-expanded="${defaultExpanded}">
            <button type="button" class="message-section-toggle" aria-expanded="${defaultExpanded}" data-closed-label="${escapeHtml(closedLabel)}" data-open-label="${escapeHtml(openLabel)}">
                <div class="message-section-toggle-copy">
                    <span class="message-section-kicker">${escapeHtml(kicker)}</span>
                    <strong class="message-section-title">${escapeHtml(title)}</strong>
                </div>
                <div class="message-section-toggle-meta">
                    <span class="message-section-count">${escapeHtml(resolvedCountLabel)}</span>
                    <span class="message-section-chevron">${defaultExpanded ? escapeHtml(openLabel) : escapeHtml(closedLabel)}</span>
                </div>
            </button>
            <div class="message-section-content" ${defaultExpanded ? "" : "hidden"}>
                <div class="message-basis-header">
                    <p class="message-basis-copy">${escapeHtml(copy)}</p>
                </div>
                ${contentHtml}
            </div>
        </section>
    `;
}

function syncPendingWorkflowTrace(workflowSteps = [], options = {}) {
    const traceList = chatStream?.querySelector(".message-pending .thinking-trace-list");
    if (!traceList) {
        return;
    }

    const visibleSteps = buildVisibleWorkflowSteps(workflowSteps, options.currentStage || chatStream?.querySelector(".message-pending #pending-stage-label")?.textContent || "", {
        includeCurrentStage: true,
    });

    if (!visibleSteps.length) {
        traceList.innerHTML = '<div class="thinking-trace-empty">会用阶段总览和完整步骤 chips 显示当前 workflow 走到哪一环。</div>';
        return;
    }

    traceList.innerHTML = buildPendingWorkflowTraceCompactHtml(visibleSteps, {
        animate: options.animateNewItems !== false,
    });

    chatStream.scrollTop = chatStream.scrollHeight;
}

function buildPendingWorkflowTraceCompactHtml(steps, options = {}) {
    const latestStep = steps[steps.length - 1] || null;
    if (!latestStep) {
        return '<div class="thinking-trace-empty">会用阶段图标和简短状态提示当前处理进展。</div>';
    }

    const completedSteps = steps.filter((step) => step?.status !== "active");
    const activeStepIndex = steps.findIndex((step) => step?.status === "active");
    const currentStepIndex = activeStepIndex >= 0 ? activeStepIndex : Math.max(steps.length - 1, 0);
    const phaseStates = deriveWorkflowPhaseStates({
        currentStage: latestStep.title,
        workflowSteps: steps,
        complete: false,
    });
    const completedPhaseCount = phaseStates.filter((phase) => phase.state === "completed").length;

    return `
        <div class="thinking-trace-compact ${options.animate ? "thinking-trace-item-enter" : ""}">
            <div class="thinking-trace-compact-current">
                <span class="thinking-trace-status">当前</span>
                <strong>${escapeHtml(latestStep?.title || "处理中")}</strong>
                ${typeof latestStep?.duration_ms === "number" ? `<span class="thinking-trace-duration">${escapeHtml(formatWorkflowDuration(latestStep.duration_ms))}</span>` : ""}
            </div>
            <div class="thinking-trace-progress-meta">
                <span>阶段 ${completedPhaseCount + 1}/${WORKFLOW_PHASE_DEFINITIONS.length}</span>
                <span>步骤 ${currentStepIndex + 1}/${steps.length}</span>
            </div>
            <p class="thinking-trace-compact-copy">${escapeHtml(latestStep?.summary || latestStep?.detail || "正在继续推进这次请求。")}</p>
            <div class="thinking-trace-chip-row">
                ${buildWorkflowChipRowHtml(steps, { compact: true, currentIndex: currentStepIndex })}
            </div>
            ${completedSteps.length ? `<p class="thinking-trace-compact-history">已完成 ${completedSteps.length} 个实际步骤，后续会继续补齐剩余环节。</p>` : ""}
        </div>
    `;
}

function buildWorkflowChipRowHtml(steps, options = {}) {
    if (!Array.isArray(steps) || !steps.length) {
        return "";
    }
    const compact = Boolean(options.compact);
    const currentIndex = Number.isInteger(options.currentIndex) ? options.currentIndex : -1;
    const groups = groupWorkflowChipsByParallel(steps);
    return groups
        .map((entry) => {
            if (entry.type === "single") {
                const { step, index } = entry;
                return buildWorkflowStepChipHtml(step, index, {
                    compact,
                    current: index === currentIndex,
                });
            }
            const branchCount = entry.items.length;
            const branchLabel = `并行 ${branchCount} 路`;
            const groupLabel = WORKFLOW_PARALLEL_GROUP_LABELS[entry.groupId] || "并行分支";
            const chips = entry.items
                .map((item) =>
                    buildWorkflowStepChipHtml(item.step, item.index, {
                        compact,
                        current: item.index === currentIndex,
                    })
                )
                .join("");
            const containerClasses = [
                "workflow-step-chip-group",
                compact ? "workflow-step-chip-group-compact" : "",
                `workflow-step-chip-group-${escapeHtml(entry.groupId)}`,
            ]
                .filter(Boolean)
                .join(" ");
            return `
                <div class="${containerClasses}" role="group" aria-label="${escapeHtml(`${groupLabel}（${branchCount} 路并行）`)}">
                    <div class="workflow-step-chip-group-head">
                        <span class="workflow-step-chip-group-icon" aria-hidden="true">⇄</span>
                        <span class="workflow-step-chip-group-label">${escapeHtml(groupLabel)}</span>
                        <span class="workflow-step-chip-group-count">${escapeHtml(branchLabel)}</span>
                    </div>
                    <div class="workflow-step-chip-group-branches">${chips}</div>
                </div>
            `;
        })
        .join("");
}

function groupWorkflowChipsByParallel(steps) {
    const groups = [];
    let cursor = null;
    steps.forEach((step, index) => {
        const groupId = typeof step?.parallel_group === "string" && step.parallel_group
            ? step.parallel_group
            : null;
        if (!groupId) {
            groups.push({ type: "single", step, index });
            cursor = null;
            return;
        }
        if (cursor && cursor.groupId === groupId) {
            cursor.items.push({ step, index });
            return;
        }
        cursor = { type: "group", groupId, items: [{ step, index }] };
        groups.push(cursor);
    });
    return groups;
}

const WORKFLOW_PARALLEL_GROUP_LABELS = {
    retrieval: "上下文检索",
    post_answer: "答后处理",
};

function buildWorkflowStepChipHtml(step, index, options = {}) {
    const title = step?.title || `步骤 ${index + 1}`;
    const displayTitle = formatWorkflowStepChipTitle(step, title);
    const status = options.current ? "active" : normalizeWorkflowStepStatus(step?.status);
    const duration = typeof step?.duration_ms === "number" ? formatWorkflowDuration(step.duration_ms) : "";
    const tooltip = [title, step?.summary || step?.detail || ""].filter(Boolean).join(" · ");
    const classNames = [
        "workflow-step-chip",
        options.compact ? "workflow-step-chip-compact" : "",
        `workflow-step-chip-${status}`,
        options.current ? "workflow-step-chip-current" : "",
    ].filter(Boolean).join(" ");
    return `
        <span class="${classNames}" title="${escapeHtml(tooltip)}">
            <span class="workflow-step-chip-index">${escapeHtml(String(index + 1))}</span>
            <span class="workflow-step-chip-title">${escapeHtml(displayTitle)}</span>
            ${duration ? `<span class="workflow-step-chip-duration">${escapeHtml(duration)}</span>` : ""}
        </span>
    `;
}

function formatWorkflowStepChipTitle(step, fallbackTitle) {
    const shortLabel = WORKFLOW_STEP_SHORT_LABELS[String(step?.key || "")];
    const title = shortLabel || fallbackTitle || "处理中";
    if (title.length <= MAX_WORKFLOW_STEP_TITLE_LENGTH) {
        return title;
    }
    return `${title.slice(0, MAX_WORKFLOW_STEP_TITLE_LENGTH)}...`;
}

function normalizeWorkflowStepStatus(status) {
    if (status === "skipped") {
        return "skipped";
    }
    if (status === "active") {
        return "active";
    }
    return "completed";
}

function appendPendingWorkflowTraceItems(traceList, steps, options = {}) {
    if (!traceList || !Array.isArray(steps) || !steps.length) {
        return;
    }

    steps.forEach((step, index) => {
        const wrapper = document.createElement("div");
        wrapper.innerHTML = buildPendingWorkflowTraceItemHtml(step, index === steps.length - 1);
        const element = wrapper.firstElementChild;
        if (!(element instanceof HTMLElement)) {
            return;
        }
        if (options.animate) {
            element.classList.add("thinking-trace-item-enter");
        }
        traceList.appendChild(element);
    });
}

function buildPendingWorkflowTraceItemHtml(step, isLatest = false) {
    const statusLabel = isLatest ? "进行中" : "已完成";
    return `
        <article class="thinking-trace-item ${isLatest ? "thinking-trace-item-latest" : ""}" data-step-key="${escapeHtml(getPendingWorkflowTraceKey(step))}">
            <div class="thinking-trace-title-row">
                <div class="thinking-trace-title-copy">
                    <strong>${escapeHtml(step?.title || "处理中")}</strong>
                    <span class="thinking-trace-status">${escapeHtml(statusLabel)}</span>
                </div>
                ${typeof step?.duration_ms === "number" ? `<span class="thinking-trace-duration">${escapeHtml(formatWorkflowDuration(step.duration_ms))}</span>` : ""}
            </div>
        </article>
    `;
}

function getPendingWorkflowTraceKey(step) {
    return String(step?.key || step?.title || step?.summary || "pending-step");
}

function buildWorkflowTraceMessageItemHtml(step, index) {
    return `
        <article class="message-process-item">
            <div class="message-process-head">
                <span class="message-process-index">${escapeHtml(String(index + 1))}</span>
                <div class="message-process-copy">
                    <strong>${escapeHtml(step.title || "处理中")}</strong>
                    <p>${escapeHtml(step.summary || step.detail || "")}</p>
                </div>
                ${typeof step.duration_ms === "number" ? `<span class="message-process-duration">${escapeHtml(formatWorkflowDuration(step.duration_ms))}</span>` : ""}
            </div>
        </article>
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
    if (!container || container.__feedbackHandlersBound) {
        return;
    }
    container.__feedbackHandlersBound = true;
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
        plannerPreview:
            meta.plannerPreview !== undefined ? meta.plannerPreview : latestWorkflowMeta.plannerPreview,
        shadowPlannerPreview:
            meta.shadowPlannerPreview !== undefined ? meta.shadowPlannerPreview : latestWorkflowMeta.shadowPlannerPreview,
        plannerComparison:
            meta.plannerComparison !== undefined ? meta.plannerComparison : latestWorkflowMeta.plannerComparison,
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
        plannerPreview: latestWorkflowMeta.plannerPreview,
        shadowPlannerPreview: latestWorkflowMeta.shadowPlannerPreview,
        plannerComparison: latestWorkflowMeta.plannerComparison,
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
        plannerPreview: null,
        shadowPlannerPreview: null,
        plannerComparison: null,
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
    if (settingsDrawer && !settingsDrawer.classList.contains("hidden")) {
        closeSettingsDrawer();
    }
    if (statusDrawer && !statusDrawer.classList.contains("hidden")) {
        closeStatusDrawer();
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
    updateComposerContextChips();
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
    clearStreamingAnswerBuffer();
    updateMobileWorkflowTrigger();
}

// Chat Latency Optimizations Task 5: lazy-create a streaming-answer-body
// container inside the pending assistant bubble and append each delta to
// it so the user sees text emerging while the LLM is still decoding. The
// final ChatResponse from the /chat POST replaces the entire pending
// bubble via renderAssistantMessage.
let streamingAnswerBuffer = "";
let streamingThinkBuffer = "";

function appendStreamingAnswerDelta(delta) {
    if (!delta) return;
    streamingAnswerBuffer += delta;
    const pending = chatStream && chatStream.querySelector(".message-pending");
    if (!pending) return;
    // Hide typing dots on first content
    const dots = pending.querySelector("#pending-typing-dots");
    if (dots) dots.hidden = true;

    // Parse <think>...</think> from the accumulated buffer
    const parsed = parseStreamingThinkContent(streamingAnswerBuffer);

    // Show thinking text if present
    if (parsed.think) {
        const section = pending.querySelector("#pending-thinking-text");
        if (section) {
            section.hidden = false;
            const thinkBody = section.querySelector(".thinking-text-body");
            if (thinkBody) {
                thinkBody.textContent = parsed.think;
                thinkBody.scrollTop = thinkBody.scrollHeight;
            }
        }
    }

    // Show main content (excluding think tags)
    const mainContent = parsed.main.trimStart();
    if (mainContent) {
        let body = pending.querySelector(".streaming-answer-body");
        if (!body) {
            body = document.createElement("div");
            body.className = "streaming-answer-body message-body";
            const frame = pending.querySelector(".message-frame") || pending;
            frame.appendChild(body);
        }
        body.textContent = mainContent;
    }
}

// Parse <think>...</think> from raw streaming content.
// Handles incomplete tags (still streaming inside <think>).
function parseStreamingThinkContent(raw) {
    const openTag = "<think>";
    const closeTag = "</think>";
    const openIdx = raw.indexOf(openTag);
    if (openIdx === -1) {
        return { think: "", main: raw };
    }
    const closeIdx = raw.indexOf(closeTag, openIdx);
    if (closeIdx === -1) {
        // Still inside <think> block (not yet closed)
        return {
            think: raw.slice(openIdx + openTag.length),
            main: raw.slice(0, openIdx),
        };
    }
    // Closed <think> block — extract and rejoin
    return {
        think: raw.slice(openIdx + openTag.length, closeIdx),
        main: raw.slice(0, openIdx) + raw.slice(closeIdx + closeTag.length),
    };
}

function appendStreamingThinkDelta(delta) {
    if (!delta) return;
    streamingThinkBuffer += delta;
    const pending = chatStream && chatStream.querySelector(".message-pending");
    if (!pending) return;
    // Hide typing dots on first content
    const dots = pending.querySelector("#pending-typing-dots");
    if (dots) dots.hidden = true;
    const section = pending.querySelector("#pending-thinking-text");
    if (!section) return;
    section.hidden = false;
    const body = section.querySelector(".thinking-text-body");
    if (body) {
        body.textContent = streamingThinkBuffer;
        body.scrollTop = body.scrollHeight;
    }
}

function clearStreamingAnswerBuffer() {
    streamingAnswerBuffer = "";
    streamingThinkBuffer = "";
}

function handleWorkflowStreamEvent(payload) {
    if (!payload || typeof payload !== "object") {
        return;
    }

    // Chat Latency Optimizations Task 4: backend emits a typed keepalive
    // every ~15s while /chat is in-flight so Cloudflare doesn't drop the
    // SSE connection mid-answer. Ignore them on the client.
    if (payload.type === "keepalive") {
        return;
    }

    if (payload.type === "trace-step" && payload.step) {
        activeWorkflowSteps = [...activeWorkflowSteps, payload.step];
        // Hide typing dots on first trace-step
        const dots = chatStream?.querySelector(".message-pending #pending-typing-dots");
        if (dots) dots.hidden = true;
        updatePendingAssistantMessage(payload.step.title || "处理中", activeWorkflowSteps);
        renderWorkflowTrace(activeWorkflowSteps, {
            workflowAction: latestWorkflowMeta.workflowAction,
            knowledgeHits: latestWorkflowMeta.knowledgeHits,
            isStreaming: true,
            currentLabel: payload.step.title,
            plannerPreview: latestWorkflowMeta.plannerPreview,
            shadowPlannerPreview: latestWorkflowMeta.shadowPlannerPreview,
            plannerComparison: latestWorkflowMeta.plannerComparison,
        });
        return;
    }

    // Chat Latency Optimizations Task 5: stream answer tokens. The /chat
    // POST still returns the final structured ChatResponse and the
    // resolved promise paints the canonical bubble via
    // ``renderAssistantMessage``; the streamed text is purely for
    // perceived-latency feedback while the LLM is decoding.
    if (payload.type === "answer_delta" && typeof payload.text === "string") {
        appendStreamingAnswerDelta(payload.text);
        return;
    }

    // Task 3: Stream reasoning/thinking tokens to the thinking-text panel
    if (payload.type === "reasoning_delta" && typeof payload.text === "string") {
        appendStreamingThinkDelta(payload.text);
        return;
    }

    if (payload.type === "answer_done") {
        // The /chat POST resolution will swap the pending bubble for the
        // fully-rendered ChatResponse, so we just clear the streaming
        // buffer here.
        clearStreamingAnswerBuffer();
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
    const closedLabel = toggle.dataset.closedLabel || "查看";
    const openLabel = toggle.dataset.openLabel || "收起";
    toggle.setAttribute("aria-expanded", String(nextExpanded));
    section.dataset.expanded = String(nextExpanded);
    content.hidden = !nextExpanded;
    if (chevron) {
        chevron.textContent = nextExpanded ? openLabel : closedLabel;
    }
}

// Task 4: Copy-to-clipboard handler (delegated on chatStream)
function handleCopyAnswerClick(event) {
    const button = event.target.closest("[data-copy-answer]");
    if (!button || !chatStream || !chatStream.contains(button)) {
        return;
    }
    const replyBlock = button.closest(".message-reply-block");
    const body = replyBlock?.querySelector(".message-body");
    if (!body) return;
    const text = body.innerText || body.textContent || "";
    navigator.clipboard.writeText(text).then(() => {
        button.classList.add("copied");
        button.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
        globalThis.setTimeout(() => {
            button.classList.remove("copied");
            button.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
        }, 2000);
    }).catch(() => { });
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
    updateWorkflowPlanSummary(meta.plannerPreview, meta.shadowPlannerPreview, meta.plannerComparison, meta.isStreaming);
    updateMobileWorkflowTrigger(meta, steps);
}

function updateWorkflowPlanComparison(comparison) {
    if (!workflowPlanCompareHeading || !workflowPlanCompareCopy) {
        return;
    }

    if (!comparison) {
        workflowPlanCompareHeading.textContent = "方案对照";
        workflowPlanCompareCopy.textContent = "只有存在对照结果时，这里才会说明两套方案是否一致。";
        if (workflowPlanCompareBadge) {
            workflowPlanCompareBadge.textContent = "对照";
            workflowPlanCompareBadge.className = "workflow-plan-badge workflow-plan-badge-idle";
        }
        if (workflowPlanCompareDetails) {
            workflowPlanCompareDetails.hidden = true;
            workflowPlanCompareDetails.open = false;
        }
        if (workflowPlanCompareSteps) {
            workflowPlanCompareSteps.innerHTML = "";
        }
        return;
    }

    const sharedSteps = Array.isArray(comparison.shared_steps) ? comparison.shared_steps : [];
    const deterministicOnlySteps = Array.isArray(comparison.deterministic_only_steps)
        ? comparison.deterministic_only_steps
        : [];
    const shadowOnlySteps = Array.isArray(comparison.shadow_only_steps) ? comparison.shadow_only_steps : [];
    const diffChips = [
        ...deterministicOnlySteps.map((stepId) => ({ prefix: "D", stepId })),
        ...shadowOnlySteps.map((stepId) => ({ prefix: "S", stepId })),
    ];

    workflowPlanCompareHeading.textContent = formatPlannerComparisonHeading(comparison.comparison_status);
    workflowPlanCompareCopy.textContent = formatPlannerComparisonSummary(comparison);
    if (workflowPlanCompareBadge) {
        workflowPlanCompareBadge.textContent = formatPlannerComparisonBadge(comparison.comparison_status);
        workflowPlanCompareBadge.className = "workflow-plan-badge workflow-plan-badge-compare";
    }
    if (workflowPlanCompareToggle) {
        workflowPlanCompareToggle.textContent = diffChips.length
            ? `查看差异步骤 (${diffChips.length})`
            : `查看共有步骤 (${sharedSteps.length})`;
    }
    if (workflowPlanCompareDetails) {
        workflowPlanCompareDetails.hidden = !diffChips.length && !sharedSteps.length;
    }
    if (workflowPlanCompareSteps) {
        const chipSource = diffChips.length
            ? diffChips.map(
                ({ prefix, stepId }) => `
                    <span class="workflow-plan-chip">
                        <span class="workflow-plan-chip-index">${escapeHtml(prefix === "D" ? "实" : "对")}</span>
                        <span>${escapeHtml(formatWorkflowPlanStepLabel(stepId))}</span>
                    </span>
                `
            )
            : sharedSteps.map(
                (stepId, index) => `
                    <span class="workflow-plan-chip">
                        <span class="workflow-plan-chip-index">${index + 1}</span>
                        <span>${escapeHtml(formatWorkflowPlanStepLabel(stepId))}</span>
                    </span>
                `
            );
        workflowPlanCompareSteps.innerHTML = chipSource.join("");
    }
}

function formatPlannerComparisonHeading(status) {
    switch (status) {
        case "shadow_disabled":
            return "当前处理方式";
        case "shadow_error":
            return "系统改用稳妥路径";
        case "equivalent":
            return "处理方式已确认";
        case "different_steps":
            return "系统补充做了一次校验";
        case "different_goal":
            return "系统采用了更稳妥的处理方式";
        default:
            return "处理说明";
    }
}

function formatPlannerComparisonBadge(status) {
    switch (status) {
        case "shadow_disabled":
            return "说明";
        case "shadow_error":
            return "已保护";
        case "equivalent":
            return "已确认";
        case "different_steps":
            return "已校验";
        case "different_goal":
            return "已调整";
        default:
            return "说明";
    }
}

function formatPlannerComparisonSummary(comparison) {
    switch (comparison.comparison_status) {
        case "shadow_error":
            return "系统在后台做补充校验时没有完成，所以这次直接沿用已确认的稳妥路径，不影响你现在看到的回复。";
        case "equivalent":
            return "系统内部的补充校验结果与当前处理方式一致，所以本轮回复按既定路径完成。";
        case "different_steps":
            return "系统在组织回复前又补充检查了一次准备顺序，但最终仍沿用当前这条处理路径，不会改变这次回答的结论。";
        case "different_goal":
            return "系统评估过另一种回复组织方式，但最终保留了更稳妥的当前方案，所以你看到的是已经收敛后的结果。";
        case "shadow_disabled":
            return "这里展示的是本次实际采用的处理方式。";
        default:
            return comparison.summary || "这里会补充说明系统这次为什么这样组织回答。";
    }
}

function updateWorkflowPlanSummary(plannerPreview, shadowPlannerPreview) {
    const comparison = arguments.length >= 3 ? arguments[2] : latestWorkflowMeta.plannerComparison;
    const isStreaming = arguments.length >= 4 ? arguments[3] : latestWorkflowMeta.isStreaming;
    syncWorkflowPlannerVisibility(plannerPreview, comparison);
    updatePlannerPreviewPanel(
        {
            heading: workflowPlanHeading,
            badge: workflowPlanBadge,
            copy: workflowPlanCopy,
            details: workflowPlanDetails,
            toggle: workflowPlanToggle,
            steps: workflowPlanSteps,
        },
        plannerPreview,
        {
            idleHeading: "这次回答的组织方式",
            idleCopy: "这里会用一句话说明这次回答是怎么组织出来的。",
            idleBadge: "说明",
            idleBadgeClass: "workflow-plan-badge workflow-plan-badge-idle",
            acceptedBadge: isStreaming ? "处理中" : "已采用",
            fallbackBadge: "备用",
            disabledBadge: "未启用",
            disabledBadgeClass: "workflow-plan-badge workflow-plan-badge-shadow",
            isShadow: false,
        }
    );
    updateWorkflowPlanNote(comparison, shadowPlannerPreview);
    if (workflowPlanCard) {
        workflowPlanCard.dataset.state = deriveWorkflowPlanCardState(plannerPreview, comparison, isStreaming);
    }
    updateWorkflowPlanCardEmphasis(plannerPreview, comparison, isStreaming);
}

function updatePlannerPreviewPanel(elements, plannerPreview, options) {
    const { heading, badge, copy, details, toggle, steps } = elements;
    if (!heading || !copy) {
        return;
    }

    if (!plannerPreview) {
        heading.textContent = options.idleHeading;
        copy.textContent = options.idleCopy;
        if (badge) {
            badge.textContent = options.idleBadge;
            badge.className = options.idleBadgeClass;
        }
        if (details) {
            details.hidden = true;
            details.open = false;
        }
        if (steps) {
            steps.innerHTML = "";
        }
        return;
    }

    const plannedSteps = Array.isArray(plannerPreview.planned_steps) ? plannerPreview.planned_steps : [];
    const isDisabledShadow = isShadowPreviewDisabled(plannerPreview);
    const acceptanceLabel = isDisabledShadow
        ? options.disabledBadge
        : (plannerPreview.accepted ? options.acceptedBadge : options.fallbackBadge);

    heading.textContent = formatPlannerGoalHeading(plannerPreview.goal, {
        accepted: Boolean(plannerPreview.accepted),
        isShadow: Boolean(options.isShadow),
    });
    if (badge) {
        badge.textContent = acceptanceLabel;
        badge.className = isDisabledShadow
            ? options.disabledBadgeClass
            : plannerPreview.accepted
                ? "workflow-plan-badge workflow-plan-badge-accepted"
                : "workflow-plan-badge workflow-plan-badge-fallback";
    }
    copy.textContent = formatPlannerPreviewSummary(plannerPreview, plannedSteps, {
        isShadow: Boolean(options.isShadow),
        isDisabledShadow,
    });

    if (toggle) {
        toggle.textContent = plannedSteps.length
            ? `展开过程说明 (${plannedSteps.length})`
            : "没有额外过程说明";
    }
    if (details) {
        details.hidden = !plannedSteps.length;
    }
    if (steps) {
        steps.innerHTML = plannedSteps
            .map(
                (stepId, index) => `
                    <span class="workflow-plan-chip">
                        <span class="workflow-plan-chip-index">${index + 1}</span>
                        <span>${escapeHtml(formatWorkflowPlanStepLabel(stepId))}</span>
                    </span>
                `
            )
            .join("");
    }
}

function syncWorkflowPlannerVisibility(plannerPreview, comparison) {
    const showPlanCard = shouldShowWorkflowPlanCard(plannerPreview, comparison);

    if (workflowPlanCard) {
        workflowPlanCard.hidden = !showPlanCard;
    }
    if (!showPlanCard) {
        resetWorkflowPlanCardEmphasis();
    }
}

function hasVisiblePlannerComparison(comparison) {
    return Boolean(comparison) && comparison.comparison_status !== "shadow_disabled";
}

function shouldShowWorkflowPlanCard(plannerPreview, comparison) {
    if (plannerPreview && plannerPreview.accepted === false) {
        return true;
    }

    if (!comparison) {
        return false;
    }

    return ["different_steps", "different_goal", "shadow_error"].includes(comparison.comparison_status);
}

function hasVisibleShadowPreview(plannerPreview) {
    return Boolean(plannerPreview)
        && !isShadowPreviewDisabled(plannerPreview)
        && plannerPreview.goal !== "shadow planner pending"
        && plannerPreview.goal !== "shadow planner error";
}

function isShadowPreviewDisabled(plannerPreview) {
    return plannerPreview.planner_mode === "llm_shadow"
        && Array.isArray(plannerPreview.validation_errors)
        && plannerPreview.validation_errors.includes("shadow planner disabled")
        && (!Array.isArray(plannerPreview.planned_steps) || !plannerPreview.planned_steps.length);
}

function formatPlannerGoalLabel(goal) {
    const goalLabels = {
        explain_admin_boundary: "说明权限边界",
        prepare_booking_agenda: "提醒先准备预约信息",
        prepare_booking_request: "整理预约请求",
        answer_research_question: "回答研究相关问题",
        respond_simple_greeting: "简短回应",
        answer_course_question: "回答课程相关问题",
        answer_grounded_question: "基于现有资料回答",
    };
    return goalLabels[goal] || String(goal || "处理当前问题").replace(/_/g, " ");
}

function formatPlannerGoalHeading(goal, options = {}) {
    const label = formatPlannerGoalLabel(goal);
    if (options.isShadow) {
        return `系统内部还评估了另一种“${label}”的组织方式`;
    }
    if (options.accepted) {
        return `这次回答会按“${label}”来组织`;
    }
    return `这次回答原本按“${label}”组织，但会在必要时改用更稳妥的处理方式`;
}

function formatPlannerFallbackLabel(template) {
    const fallbackLabels = {
        review_queue: "请老师本人确认后再处理",
        advise_only: "先给你准备建议",
        book_meeting: "继续走预约流程",
        answer_question: "直接给出回复",
    };
    return fallbackLabels[template] || String(template || "直接回答").replace(/_/g, " ");
}

function formatPlannerPreviewSummary(plannerPreview, plannedSteps, options) {
    if (options.isDisabledShadow) {
        return "当前只保留本次实际采用的处理方式。";
    }

    const stepSummary = formatPlannerStepFlowSummary(plannedSteps);
    if (options.isShadow) {
        return `${stepSummary}。这只是系统内部的补充校验，不会真正影响这次回复。`;
    }

    const parts = [stepSummary];
    if (!plannerPreview.accepted) {
        parts.push(`如果当前信息不足，系统会改用“${formatPlannerFallbackLabel(plannerPreview.fallback_template)}”这种更稳妥的处理方式`);
    }
    if (plannerPreview.fallback_reason) {
        parts.push(`原因：${plannerPreview.fallback_reason}`);
    }
    return parts.join("；");
}

function formatPlannerStepFlowSummary(plannedSteps) {
    if (!plannedSteps.length) {
        return "系统会直接基于当前信息组织回复";
    }

    const stepLabels = plannedSteps.slice(0, 2).map((stepId) => formatWorkflowPlanStepLabel(stepId));
    if (plannedSteps.length === 1) {
        return `系统会先${stepLabels[0]}，再给出回复`;
    }
    if (plannedSteps.length === 2) {
        return `系统会先${stepLabels[0]}，再${stepLabels[1]}，最后组织回复`;
    }
    return `系统会先${stepLabels[0]}、${stepLabels[1]}等 ${plannedSteps.length} 个步骤，再组织最终回复`;
}

function updateWorkflowPlanNote(comparison, shadowPlannerPreview) {
    if (!workflowPlanNote) {
        return;
    }

    const note = formatPlannerComparisonInlineNote(comparison, shadowPlannerPreview);
    workflowPlanNote.hidden = !note;
    workflowPlanNote.textContent = note || "";
}

function formatPlannerComparisonInlineNote(comparison, shadowPlannerPreview) {
    if (!comparison) {
        return hasVisibleShadowPreview(shadowPlannerPreview)
            ? "补充说明：系统还会在后台做一次补充校验，但不会影响这次实际回答。"
            : "";
    }

    switch (comparison.comparison_status) {
        case "shadow_error":
            return "补充说明：后台补充校验这次没有跑完，但不影响你现在看到的回答。";
        case "equivalent":
            return "补充说明：后台补充校验结果与当前处理方式一致。";
        case "different_steps":
            return "补充说明：系统还试了一种不同的准备顺序，但没有改动这次实际回答。";
        case "different_goal":
            return "补充说明：系统还评估了另一种回答组织思路，但最终没有采用。";
        default:
            return "";
    }
}

function deriveWorkflowPlanCardState(plannerPreview, comparison, isStreaming) {
    if (isStreaming) {
        return "active";
    }
    if (comparison?.comparison_status === "shadow_error") {
        return "attention";
    }
    if (comparison && comparison.comparison_status !== "shadow_disabled") {
        return "compare";
    }
    if (plannerPreview && !plannerPreview.accepted) {
        return "attention";
    }
    return "complete";
}

function updateWorkflowPlanCardEmphasis(plannerPreview, comparison, isStreaming) {
    if (!workflowPlanCard || workflowPlanCard.hidden) {
        resetWorkflowPlanCardEmphasis();
        return;
    }

    const signature = buildWorkflowPlanCardSignature(plannerPreview, comparison);
    const changed = signature !== workflowPlanLastSignature;
    workflowPlanLastSignature = signature;

    workflowPlanCard.classList.toggle("workflow-plan-card-live", Boolean(isStreaming));

    if (isStreaming) {
        clearWorkflowPlanDecayTimer();
        workflowPlanCard.classList.remove("workflow-plan-card-settled");
        if (changed) {
            replayWorkflowPlanCardReveal();
        }
        return;
    }

    if (changed) {
        replayWorkflowPlanCardReveal();
    }
    workflowPlanCard.classList.remove("workflow-plan-card-live");
    workflowPlanCard.classList.remove("workflow-plan-card-settled");
    clearWorkflowPlanDecayTimer();
    workflowPlanDecayTimer = globalThis.setTimeout(() => {
        workflowPlanCard?.classList.add("workflow-plan-card-settled");
        workflowPlanDecayTimer = null;
    }, 4200);
}

function buildWorkflowPlanCardSignature(plannerPreview, comparison) {
    return JSON.stringify({
        goal: plannerPreview?.goal || null,
        accepted: plannerPreview?.accepted || false,
        fallbackTemplate: plannerPreview?.fallback_template || null,
        plannedSteps: Array.isArray(plannerPreview?.planned_steps) ? plannerPreview.planned_steps : [],
        comparisonStatus: comparison?.comparison_status || null,
        comparisonSummary: comparison?.summary || null,
    });
}

function replayWorkflowPlanCardReveal() {
    if (!workflowPlanCard) {
        return;
    }
    workflowPlanCard.classList.remove("workflow-plan-card-reveal");
    void workflowPlanCard.offsetWidth;
    workflowPlanCard.classList.add("workflow-plan-card-reveal");
}

function clearWorkflowPlanDecayTimer() {
    if (workflowPlanDecayTimer !== null) {
        globalThis.clearTimeout(workflowPlanDecayTimer);
        workflowPlanDecayTimer = null;
    }
}

function resetWorkflowPlanCardEmphasis() {
    clearWorkflowPlanDecayTimer();
    workflowPlanLastSignature = "";
    if (!workflowPlanCard) {
        return;
    }
    workflowPlanCard.classList.remove("workflow-plan-card-live", "workflow-plan-card-settled", "workflow-plan-card-reveal");
}

function formatWorkflowPlanStepLabel(stepId) {
    const labels = {
        answer_with_citations: "带依据回答",
        assemble_prompt_context: "组装上下文",
        classify_intent: "识别意图",
        create_escalation_draft: "生成人工升级草稿",
        detect_knowledge_gap: "检查知识缺口",
        detect_profile_context: "识别身份场景",
        draft_booking_request: "生成预约草稿",
        draft_follow_up_action: "生成后续动作草稿",
        draft_knowledge_gap: "生成知识缺口草稿",
        record_conversation_memory: "写回对话记忆",
        render_user_response: "组织返回结果",
        retrieve_knowledge: "检索知识资料",
        retrieve_profile_memory: "检索长期记忆",
        retrieve_recent_memory: "检索近期记忆",
    };
    return labels[stepId] || String(stepId || "").replaceAll("_", " ");
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
    const currentAssistantName = document.getElementById("assistant-name");
    if (currentAssistantName) {
        currentAssistantName.textContent = assistantLabel;
    }
    if (topbarTitle) {
        topbarTitle.textContent = formatWorkspaceTitle(ownerName);
    }
    if (topbarSubtitle) {
        topbarSubtitle.textContent = formatWorkspaceSubtitle(ownerName, ownerRole);
    }
    if (homepageLink) {
        const normalizedHomepageUrl = homepageUrl ? String(homepageUrl).trim() : "";
        homepageLink.hidden = false;
        homepageLink.href = normalizedHomepageUrl || "/home/";
    }
    if (chatQuestion) {
        chatQuestion.placeholder = "直接说问题；预约请写 agenda、blocker 和 draft。";
    }
}

function syncIntroCardPresentation() {
    const currentAssistantName = document.getElementById("assistant-name");
    if (currentAssistantName) {
        currentAssistantName.textContent = assistantLabel;
    }
    applyVisitorProfilePresentation({ syncCourseContext: true });
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
        return "学术分身";
    }
    return normalizedOwnerName;
}

function formatWorkspaceSubtitle(ownerName, ownerRole) {
    const normalizedOwnerName = ownerName ? String(ownerName).trim() : "";
    const normalizedOwnerRole = ownerRole ? String(ownerRole).trim() : "";
    if (!normalizedOwnerName) {
        return "课程、研究、预约。";
    }
    if (normalizedOwnerRole) {
        return `${normalizedOwnerName} · ${normalizedOwnerRole}`;
    }
    return `${normalizedOwnerName}的线上办公室。`;
}

function openModal(element) {
    if (!element) {
        return;
    }
    closeWorkflowMobileSheet();
    modalOverlay.classList.remove("hidden");
    element.classList.remove("hidden");
    element.setAttribute("aria-hidden", "false");
    syncFloatingWorkflowTriggerState();
}

function closeModals() {
    modalOverlay.classList.add("hidden");
    overlayModals.forEach((element) => {
        element.classList.add("hidden");
        element.setAttribute("aria-hidden", "true");
    });
    closeDrawers();
    syncFloatingWorkflowTriggerState();
}

function openSettingsDrawer() {
    closeWorkflowMobileSheet();
    closeMobileTopbarActions();
    closeStatusDrawer();
    settingsDrawer.classList.remove("hidden");
    settingsDrawer.setAttribute("aria-hidden", "false");
    document.body.classList.add("drawer-pinned");
    if (isDrawerOverlayViewport()) {
        modalOverlay.classList.remove("hidden");
    } else if (!hasVisibleOverlayModal()) {
        modalOverlay.classList.add("hidden");
    }
    syncFloatingWorkflowTriggerState();
}

function closeSettingsDrawer() {
    settingsDrawer.classList.add("hidden");
    settingsDrawer.setAttribute("aria-hidden", "true");
    document.body.classList.remove("drawer-pinned");
    if (!hasVisibleOverlayModal() && isStatusDrawerClosed()) {
        modalOverlay.classList.add("hidden");
    }
    syncFloatingWorkflowTriggerState();
}

function openStatusDrawer() {
    closeWorkflowMobileSheet();
    closeMobileTopbarActions();
    statusDrawer.classList.remove("hidden");
    statusDrawer.setAttribute("aria-hidden", "false");
    if (isDrawerOverlayViewport()) {
        modalOverlay.classList.remove("hidden");
    } else if (!hasVisibleOverlayModal() && isSettingsDrawerClosed()) {
        modalOverlay.classList.add("hidden");
    }
    syncFloatingWorkflowTriggerState();
}

function closeStatusDrawer() {
    statusDrawer.classList.add("hidden");
    statusDrawer.setAttribute("aria-hidden", "true");
    if (!hasVisibleOverlayModal() && isSettingsDrawerClosed()) {
        modalOverlay.classList.add("hidden");
    }
    syncFloatingWorkflowTriggerState();
}

function closeDrawers() {
    closeSettingsDrawer();
    closeStatusDrawer();
}

function isSettingsDrawerClosed() {
    return !settingsDrawer || settingsDrawer.classList.contains("hidden");
}

function isStatusDrawerClosed() {
    return !statusDrawer || statusDrawer.classList.contains("hidden");
}

function areDrawersClosed() {
    return isSettingsDrawerClosed() && isStatusDrawerClosed();
}

function openDrawer() {
    openSettingsDrawer();
}

function closeDrawer() {
    closeSettingsDrawer();
}

function hasVisibleOverlayModal() {
    return overlayModals.some((element) => !element.classList.contains("hidden"));
}

function syncFloatingWorkflowTriggerState() {
    const hasOverlaySurface = !areDrawersClosed() || !modalOverlay.classList.contains("hidden");
    document.body.classList.toggle("workflow-trigger-suppressed", hasOverlaySurface);
}

function isDrawerOverlayViewport() {
    try {
        return Boolean(globalThis.matchMedia?.("(max-width: 920px)").matches);
    } catch {
        return false;
    }
}

function isMobileTopbarActionsOpen() {
    return document.body.classList.contains("mobile-topbar-actions-open");
}

function closeMobileTopbarActions() {
    if (!isMobileTopbarActionsOpen()) {
        return;
    }
    document.body.classList.remove("mobile-topbar-actions-open");
    topbarActionsToggleButton?.setAttribute("aria-expanded", "false");
}

function toggleMobileTopbarActions(event) {
    event?.stopPropagation();
    const nextOpen = !isMobileTopbarActionsOpen();
    document.body.classList.toggle("mobile-topbar-actions-open", nextOpen);
    topbarActionsToggleButton?.setAttribute("aria-expanded", String(nextOpen));
}

function handleTopbarActionsClick(event) {
    const target = event.target;
    if (!(target instanceof Element)) {
        return;
    }
    const action = target.closest("button,a");
    if (!action) {
        return;
    }
    closeMobileTopbarActions();
}

async function handleAdminLogout() {
    try {
        await apiRequest("/auth/admin/logout", { method: "POST" });
        bookingList.innerHTML = "";
        escalationList.innerHTML = "";
        memoryProfilesSummary.innerHTML = "";
        memoryProfilesList.innerHTML = "";
        operationsSummary.innerHTML = "";
        operationsWorkflowReplaySummary.innerHTML = "";
        operationsWorkflowReplayList.innerHTML = "";
        operationsQueues.innerHTML = "";
        operationsTasks.innerHTML = "";
        operationsBookings.innerHTML = "";
        operationsStudentProfiles.innerHTML = "";
        operationsSatisfaction.innerHTML = "";
        operationsGaps.innerHTML = "";
        operationsArtifactDrafts.innerHTML = "";
        operationsEscalations.innerHTML = "";
        operationsFollowUps.innerHTML = "";
        operationsSuggestions.innerHTML = "";
        questionAnalyticsSummary.innerHTML = "";
        questionAnalyticsClusters.innerHTML = "";
        questionAnalyticsGaps.innerHTML = "";
        questionAnalyticsUnresolved.innerHTML = "";
        questionAnalyticsHandoffs.innerHTML = "";
        questionAnalyticsDrafts.innerHTML = "";
        resetManagedServicePanel();
        setInlineStatus(escalationAdminResponse, "这里放必须由你亲自接手的请求。", "empty");
        setInlineStatus(memoryProfilesResponse, "需要查学生长期记录时再打开这里。", "empty");
        setInlineStatus(operationsResponse, "这里集中查看运营后台待处理事项。", "empty");
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

// Task 5: Basic markdown formatting (code blocks + inline code).
// Processes escaped HTML so XSS-safe output is preserved.
function formatMessageContent(rawText) {
    const escaped = escapeHtml(rawText);
    // Replace triple-backtick code blocks
    let formatted = escaped.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
        return `<pre>${code.trim()}</pre>`;
    });
    // Replace inline backtick code
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    return formatted;
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
updateComposerContextChips();
restoreHistoryRailState();
restoreWorkflowShellState();
syncWorkflowViewportState();

async function initializePage() {
    renderConversationHistoryList();
    applyStoredVisitorProfile();
    applyVisitorProfilePresentation({ syncCourseContext: true });
    markPresentationReady();
    startOnlinePresenceHeartbeat();
    startStatusAutoRefresh();
    await refreshStatus();
    await refreshSession();
    await refreshUserSession();
    applyVisitorProfilePresentation({ syncCourseContext: true });
    maybeOpenVisitorIdentityPrompt();
}

initializePage();