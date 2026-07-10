var CONCIERGE_PANEL_BUILD = globalThis.__CONCIERGE_PANEL_BUILD || (() => {
  let src = "";

  try {
    src = String(document.currentScript?.src || "");
  } catch (e) {
    // no-op
  }

  if (!src) {
    try {
      const scripts = Array.from(document.scripts || []);
      src = scripts
        .map((script) => String(script?.src || ""))
        .find((value) => value.includes("/concierge-static/")) || "";
    } catch (e) {
      // no-op
    }
  }

  let selectedPanel = "";
  let cacheToken = "";

  if (src) {
    try {
      const url = new URL(src, window.location.origin);
      const segments = url.pathname.split("/");
      selectedPanel = segments[segments.length - 1] || "";
      cacheToken = url.searchParams.get("v") || "";
    } catch (e) {
      // no-op
    }
  }

  return {
    src,
    selected_panel: selectedPanel,
    cache_token: cacheToken,
  };
})();
globalThis.__CONCIERGE_PANEL_BUILD = CONCIERGE_PANEL_BUILD;

var CONCIERGE_TTS_ENGINE_IDS = {
  openai_conversation: "tts.openai_tts",
  google_translate: "tts.google_translate_en_com",
};

function conciergeNormalizeVoiceEnrollmentProvider(value) {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized === "satellite" || normalized === "assist_satellite") return "satellite";
  if (normalized === "browser" || normalized === "browser_microphone" || normalized === "browser_mic") return "browser";
  return "";
}

function conciergeGetBrowserVoiceEnrollmentCapability({ isSecureContext, mediaDevices, MediaRecorderCtor }) {
  const secureContext = Boolean(isSecureContext);
  const microphoneSupported = Boolean(mediaDevices?.getUserMedia) && Boolean(MediaRecorderCtor);
  const available = secureContext && microphoneSupported;

  if (!secureContext) {
    return {
      secureContext,
      microphoneSupported,
      available,
      summary: "Microphone recording requires a secure browser context. Open Home Assistant over HTTPS or from localhost, then try again.",
    };
  }

  if (!microphoneSupported) {
    return {
      secureContext,
      microphoneSupported,
      available,
      summary: "This browser does not support microphone recording for voice enrollment.",
    };
  }

  return {
    secureContext,
    microphoneSupported,
    available,
    summary: "Browser microphone capture is available.",
  };
}

function conciergeCollectSatelliteOptions(hassStates) {
  const states = hassStates && typeof hassStates === "object" ? hassStates : {};
  return Object.entries(states)
    .filter(([entityId]) => String(entityId || "").startsWith("assist_satellite."))
    .map(([entityId, stateObj]) => ({
      entity_id: String(entityId || "").trim(),
      label: String(
        stateObj?.attributes?.friendly_name
        || stateObj?.attributes?.name
        || entityId
      ).trim() || String(entityId || "").trim(),
    }))
    .filter((option) => option.entity_id)
    .sort((left, right) => left.label.localeCompare(right.label));
}

function conciergeResolveVoiceEnrollmentDefaultProvider({ browserAvailable, satelliteCount }) {
  if (browserAvailable) return "browser";
  if (Number(satelliteCount || 0) > 0) return "satellite";
  return "browser";
}

function conciergeGetVoiceEnrollmentProviderAvailability({ browserAvailable, satelliteCount }) {
  return {
    browserSelectable: Boolean(browserAvailable),
    satelliteSelectable: Number(satelliteCount || 0) > 0,
  };
}

function conciergeIsVoiceEnrollmentAuthorized(dialogState) {
  const dialog = dialogState && typeof dialogState === "object" ? dialogState : {};
  return Boolean(dialog.consentAcknowledged) && dialog.localOnly !== false;
}

function conciergeBuildSatelliteEnrollmentPrompt(phraseIndex, speechText) {
  const ordinal = Math.max(1, Number(phraseIndex || 0) + 1);
  return `Please read phrase ${ordinal} now.`;
}

const CONCIERGE_VOICE_ENROLLMENT_CORPUS = [
  {
    prompt_id: "cmd_lights_kitchen_01",
    speech_text: "Hello Concierge, turn on the kitchen lights and set them to seventy percent.",
    prompt_category: "command",
    prompt_length_bucket: "medium",
    capture_distance: "near_field",
    capture_noise: "quiet",
  },
  {
    prompt_id: "query_living_env_02",
    speech_text: "What are the temperature and humidity in the living room right now?",
    prompt_category: "question",
    prompt_length_bucket: "medium",
    capture_distance: "mid_field",
    capture_noise: "quiet",
  },
  {
    prompt_id: "cmd_bedroom_scene_03",
    speech_text: "Set the bedroom shades halfway, then dim the lamps to thirty percent.",
    prompt_category: "command",
    prompt_length_bucket: "medium",
    capture_distance: "near_field",
    capture_noise: "moderate",
  },
  {
    prompt_id: "query_security_04",
    speech_text: "Remind me if any doors or windows are still open after ten thirty tonight.",
    prompt_category: "question",
    prompt_length_bucket: "long",
    capture_distance: "mid_field",
    capture_noise: "moderate",
  },
  {
    prompt_id: "conv_morning_digest_05",
    speech_text: "Good morning Concierge, give me a short summary of the weather and top news.",
    prompt_category: "conversational",
    prompt_length_bucket: "long",
    capture_distance: "near_field",
    capture_noise: "quiet",
  },
  {
    prompt_id: "cmd_music_office_06",
    speech_text: "Please play soft jazz in the office speaker group for fifteen minutes.",
    prompt_category: "command",
    prompt_length_bucket: "medium",
    capture_distance: "mid_field",
    capture_noise: "moderate",
  },
  {
    prompt_id: "conv_presence_07",
    speech_text: "Concierge, I am in the family room and I want a calm, detailed answer.",
    prompt_category: "conversational",
    prompt_length_bucket: "long",
    capture_distance: "near_field",
    capture_noise: "quiet",
  },
  {
    prompt_id: "query_garage_alert_08",
    speech_text: "If the garage door opens, send a message to my phone and show the driveway camera.",
    prompt_category: "question",
    prompt_length_bucket: "long",
    capture_distance: "mid_field",
    capture_noise: "moderate",
  },
  {
    prompt_id: "cmd_night_mode_09",
    speech_text: "At eleven p.m., lock the doors, turn off downstairs lights, and set the alarm to home mode.",
    prompt_category: "command",
    prompt_length_bucket: "long",
    capture_distance: "near_field",
    capture_noise: "moderate",
  },
  {
    prompt_id: "conv_daily_checkin_10",
    speech_text: "Before we finish, tell me tomorrow's first meeting and whether I left anything pending tonight.",
    prompt_category: "conversational",
    prompt_length_bucket: "long",
    capture_distance: "mid_field",
    capture_noise: "quiet",
  },
];

const CONCIERGE_VOICE_ENROLLMENT_MIN_TOTAL_DURATION_MS = 30000;
const CONCIERGE_VOICE_ENROLLMENT_MIN_ACCEPTED_UTTERANCES = 8;

function conciergeVoiceEnrollmentPrompt(index) {
  const clampedIndex = Math.max(0, Math.min(Number(index || 0), CONCIERGE_VOICE_ENROLLMENT_CORPUS.length - 1));
  const prompt = CONCIERGE_VOICE_ENROLLMENT_CORPUS[clampedIndex] || CONCIERGE_VOICE_ENROLLMENT_CORPUS[0];
  return {
    prompt_id: String(prompt.prompt_id || `prompt_${clampedIndex + 1}`).trim(),
    prompt_order: clampedIndex + 1,
    speech_text: String(prompt.speech_text || "").trim(),
    prompt_category: String(prompt.prompt_category || "conversational").trim(),
    prompt_length_bucket: String(prompt.prompt_length_bucket || "medium").trim(),
    capture_distance: String(prompt.capture_distance || "near_field").trim(),
    capture_noise: String(prompt.capture_noise || "quiet").trim(),
  };
}

function conciergeBuildVoiceEnrollmentDialogState(previousState = {}, seedState = {}) {
  const previous = previousState && typeof previousState === "object" ? previousState : {};
  const seed = seedState && typeof seedState === "object" ? seedState : {};
  const satelliteOptions = Array.isArray(seed.satelliteOptions)
    ? seed.satelliteOptions
    : (Array.isArray(previous.satelliteOptions) ? previous.satelliteOptions : []);
  const satelliteIds = satelliteOptions
    .map((option) => String(option?.entity_id || "").trim())
    .filter(Boolean);
  const browserAvailable = seed.browserAvailable !== undefined ? Boolean(seed.browserAvailable) : Boolean(previous.browserAvailable);
  let captureProvider = conciergeNormalizeVoiceEnrollmentProvider(seed.captureProvider)
    || conciergeNormalizeVoiceEnrollmentProvider(previous.captureProvider)
    || conciergeResolveVoiceEnrollmentDefaultProvider({ browserAvailable, satelliteCount: satelliteIds.length });
  if (captureProvider === "satellite" && !satelliteIds.length) {
    captureProvider = "browser";
  }

  let satelliteEntityId = String(
    seed.satelliteEntityId !== undefined ? seed.satelliteEntityId : (previous.satelliteEntityId || "")
  ).trim();
  if (satelliteIds.length === 1 && !satelliteEntityId) {
    satelliteEntityId = satelliteIds[0];
  }
  if (satelliteEntityId && !satelliteIds.includes(satelliteEntityId)) {
    satelliteEntityId = satelliteIds.length === 1 ? satelliteIds[0] : "";
  }

  return {
    open: Boolean(seed.open !== undefined ? seed.open : previous.open),
    personId: String(seed.personId !== undefined ? seed.personId : (previous.personId || "")).trim(),
    phraseIndex: Math.max(0, Number(seed.phraseIndex !== undefined ? seed.phraseIndex : (previous.phraseIndex || 0)) || 0),
    currentCaptured: Boolean(seed.currentCaptured !== undefined ? seed.currentCaptured : previous.currentCaptured),
    status: String(seed.status !== undefined ? seed.status : (previous.status || "")).trim(),
    consentAcknowledged: Boolean(seed.consentAcknowledged !== undefined ? seed.consentAcknowledged : previous.consentAcknowledged),
    localOnly: seed.localOnly !== undefined ? Boolean(seed.localOnly) : (previous.localOnly !== false),
    captureProvider,
    satelliteEntityId,
    satelliteOptions,
    browserAvailable,
    browserSecureContext: seed.browserSecureContext !== undefined ? Boolean(seed.browserSecureContext) : Boolean(previous.browserSecureContext),
    browserMicSupported: seed.browserMicSupported !== undefined ? Boolean(seed.browserMicSupported) : Boolean(previous.browserMicSupported),
    browserStatusSummary: String(seed.browserStatusSummary !== undefined ? seed.browserStatusSummary : (previous.browserStatusSummary || "")).trim(),
    progressSummary: String(seed.progressSummary !== undefined ? seed.progressSummary : (previous.progressSummary || "")).trim(),
    progress: seed.progress !== undefined ? seed.progress : (previous.progress || null),
    enrollmentSessionId: String(seed.enrollmentSessionId !== undefined ? seed.enrollmentSessionId : (previous.enrollmentSessionId || "")).trim(),
    completionReadiness: seed.completionReadiness !== undefined ? seed.completionReadiness : (previous.completionReadiness || null),
    isBusy: Boolean(seed.isBusy !== undefined ? seed.isBusy : previous.isBusy),
    busyLabel: String(seed.busyLabel !== undefined ? seed.busyLabel : (previous.busyLabel || "")).trim(),
    showProviderFallback: Boolean(seed.showProviderFallback !== undefined ? seed.showProviderFallback : previous.showProviderFallback),
    voiceProfileId: String(seed.voiceProfileId !== undefined ? seed.voiceProfileId : (previous.voiceProfileId || "")).trim(),
  };
}

var ConciergeApp = globalThis.ConciergeApp || class ConciergeApp extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._loaded = false;
    this._loadError = null;
    this._loadingPromise = null;
    this._areas = [];
    this._floors = [];
    this._rooms = {};
    this._composites = {};
    this._peopleRegistry = {};
    this._people = {};
    this._voiceProfiles = {};
    this._roomCatalog = {};
    this._compositeCatalog = {};
    this._labelRegistry = [];
    this._globalCatalog = {
      weather_entity_ids: [],
      news_entity_ids: [],
      alarm_entity_ids: [],
    };
    this._globalFeatures = {};
    this._globalContextUsage = {};
    this._integrationOptions = {
      ai_enabled: false,
      ai_local_first: true,
      action_provider: "none",
      tts_provider: "none",
      tts_enabled: false,
      media_provider: "none",
      asset_intelligence_provider: "none",
      capabilities: {
        cap_ai: false,
        cap_tts: false,
        cap_persona: false,
        cap_assets: false,
        cap_voice_enrollment: false,
        cap_extended_history: false,
      },
    };
    this._archiveStatus = {
      destination_uri: "",
      destination_configured: false,
      archive_enabled: false,
      include_reference_excerpts: false,
    };
    this._activityTimeline = [];
    this._activityTimelineLoaded = false;
    this._activityTimelineLoading = false;
    this._activityTimelineFilter = "all";
    this._activityTimelineSearch = "";
    this._assetIntelligenceConnected = false;
    this._ttsCatalogLoading = false;
    this._ttsCatalogLoaded = false;
    this._ttsCatalogLoadedAt = 0;
    this._ttsCatalogProvider = "";
    this._ttsCatalog = {
      provider: "none",
      defaultLanguage: "",
      languages: [],
      languageLabels: {},
      voicesByLanguage: {},
    };
    this._roomVoiceDialog = {
      open: false,
      areaId: "",
      message: "Hello. How can I assist?",
      playing: false,
      error: "",
    };
    this._roomVoicePreviewAudio = null;
    this._activityDetailsDialog = {
      open: false,
      areaId: "",
      activityId: "",
    };
    this._globalSettingsDialogOpen = false;
    this._mergeMode = false;
    this._mergeDraftName = "";
    this._mergeDraftAreaIds = [];
    this._editMergeCompositeId = null;
    this._editMergeName = "";
    this._editMergeAreaIds = [];
    this._editMergeError = "";
    this._activeFormDraftScope = null;
    this._activeFormDraftDirty = false;
    this._panelVersionStatus = null;
    this._panelVersionDismissed = false;
    this._panelVersionCheckInFlight = null;
    this._lastPanelVersionCheckAt = 0;
    this._editMergeDelegatesBound = false;
    this._selectedAreaId = null;
    this._selectedCompositeId = null;
    this._selectedPersonId = null;
    this._roomSectionDraftState = {};
    this._roomPersonaDraftState = {};
    this._voiceEnrollmentDialog = conciergeBuildVoiceEnrollmentDialogState({}, {
      open: false,
      personId: "",
      phraseIndex: 0,
      currentCaptured: false,
      status: "",
      consentAcknowledged: false,
      localOnly: true,
      captureProvider: "browser",
      satelliteEntityId: "",
      satelliteOptions: [],
      browserAvailable: false,
      browserSecureContext: false,
      browserMicSupported: false,
      browserStatusSummary: "",
      progressSummary: "",
      progress: null,
      enrollmentSessionId: "",
      completionReadiness: null,
      isBusy: false,
      busyLabel: "",
      showProviderFallback: false,
      voiceProfileId: "",
    });
    this._voiceEnrollmentRecording = {
      active: false,
      personId: "",
      recorder: null,
      stream: null,
      startedAt: 0,
    };
    this._lifecycleListenersBound = false;
    this._lastResumeSnapshotRefreshAt = 0;
    this._onWindowFocus = () => this._refreshSnapshotOnResume();
    this._onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        this._refreshSnapshotOnResume();
      }
    };
  }

  _refreshSnapshotOnResume() {
    if (!this._hass) return;
    if (this._loadingPromise) return;
    if (this._hasActiveVoiceEnrollmentDialog()) return;
    const now = Date.now();
    if (now - this._lastResumeSnapshotRefreshAt < 1500) return;
    this._lastResumeSnapshotRefreshAt = now;
    this._loadingPromise = this._load().finally(() => {
      this._loadingPromise = null;
    });
  }

  connectedCallback() {
    // Preserve current navigation context across panel re-attach events.
    if (this._voiceEnrollmentDialog?.open && this._voiceEnrollmentDialog?.personId) {
      this._selectedAreaId = null;
      this._selectedCompositeId = null;
      this._selectedPersonId = this._voiceEnrollmentDialog.personId;
    }
    if (!this._editMergeDelegatesBound) {
      this._editMergeDelegatesBound = true;
      this.addEventListener("click", (event) => {
        const target = event.target instanceof Element ? event.target : null;
        if (!target) return;

        const reloadButton = target.closest("[data-panel-reload]");
        if (reloadButton) {
          event.preventDefault();
          event.stopPropagation();
          this._reloadPanelPage();
          return;
        }

        const dismissButton = target.closest("[data-panel-dismiss]");
        if (dismissButton) {
          event.preventDefault();
          event.stopPropagation();
          this._panelVersionDismissed = true;
          this._render();
          return;
        }

        const openButton = target.closest("[data-edit-merge-open]");
        if (openButton) {
          event.preventDefault();
          event.stopPropagation();
          const compositeId = openButton.getAttribute("data-composite-id");
          if (compositeId) this._openEditMergeDialog(compositeId);
          return;
        }

        const assetAddButton = target.closest(".cg-asset-group-add");
        if (assetAddButton) {
          event.preventDefault();
          event.stopPropagation();
          const areaId = assetAddButton.getAttribute("data-area-id") || "";
          if (areaId) this._addAssetGroupFromDraft(areaId);
          return;
        }

        const deviceAddButton = target.closest(".cg-device-group-add");
        if (deviceAddButton) {
          event.preventDefault();
          event.stopPropagation();
          const areaId = deviceAddButton.getAttribute("data-area-id") || "";
          if (areaId) this._addRoomDeviceGroupFromDraft(areaId);
          return;
        }

        const assetDeviceRemoveButton = target.closest(".cg-asset-device-remove");
        if (assetDeviceRemoveButton) {
          event.preventDefault();
          event.stopPropagation();
          const row = assetDeviceRemoveButton.closest(".cg-asset-group-row");
          const deviceId = String(assetDeviceRemoveButton.getAttribute("data-device-id") || "").trim();
          if (row && deviceId) this._removeAssetDeviceFromGroupRow(row, deviceId);
          return;
        }

        const deviceRemoveButton = target.closest(".cg-room-device-remove");
        if (deviceRemoveButton) {
          event.preventDefault();
          event.stopPropagation();
          const row = deviceRemoveButton.closest(".cg-device-group-row");
          const entityId = String(deviceRemoveButton.getAttribute("data-entity-id") || "").trim();
          if (row && entityId) this._removeRoomDeviceFromGroupRow(row, entityId);
          return;
        }

        const assetRemoveButton = target.closest(".cg-asset-group-remove");
        if (assetRemoveButton) {
          event.preventDefault();
          event.stopPropagation();
          const row = assetRemoveButton.closest(".cg-asset-group-row");
          if (row) this._removeAssetGroupRow(row);
          return;
        }

        const closeButton = target.closest("[data-edit-merge-close], [data-edit-merge-cancel]");
        if (closeButton) {
          event.preventDefault();
          event.stopPropagation();
          this._closeEditMergeDialog();
          return;
        }

        const updateButton = target.closest("[data-edit-merge-update]");
        if (updateButton) {
          event.preventDefault();
          event.stopPropagation();
          this._saveEditMergeDialog();
          return;
        }
      });

      this.addEventListener("input", (event) => {
        const target = event.target instanceof Element ? event.target : null;
        if (!target) return;

        if (target.matches("#cg-edit-merge-name")) {
          this._editMergeName = target.value || "";
        }

        if (this._isTrackedDataCaptureTarget(target)) {
          this._markActiveFormDraftDirty();
          const areaId = target.getAttribute("data-area-id") || "";
          const fieldKey = target.getAttribute("data-field-key") || "";
          const section = target.getAttribute("data-room-section") || this._roomSectionForFieldKey(target.getAttribute("data-field-key") || "");
          if (areaId && section === "persona" && fieldKey) {
            this._setRoomPersonaDraftField(areaId, fieldKey, target.value ?? "");
          }
          if (areaId && this._shouldAutoMarkSectionDirty(section, fieldKey)) {
            this._markRoomSectionDraftDirty(areaId, section);
          }
          if (areaId && fieldKey === "asset_groups") {
            this._syncRoomAssetGroupAddButtonState(areaId);
          }
          if (areaId && fieldKey === "device_groups") {
            this._syncRoomDeviceGroupAddButtonState(areaId);
          }
        }
      });

      this.addEventListener("change", (event) => {
        const target = event.target instanceof Element ? event.target : null;
        if (!target) return;

        if (target.matches(".cg-edit-merge-room")) {
          this._editMergeError = "";
          this._syncEditMergeSelectionFromDom();
        }

        if (this._isTrackedDataCaptureTarget(target)) {
          this._markActiveFormDraftDirty();
          const areaId = target.getAttribute("data-area-id") || "";
          const fieldKey = target.getAttribute("data-field-key") || "";
          const section = target.getAttribute("data-room-section") || this._roomSectionForFieldKey(target.getAttribute("data-field-key") || "");
          if (areaId && section === "persona" && fieldKey) {
            this._setRoomPersonaDraftField(areaId, fieldKey, target.value ?? "");
            if (fieldKey === "tts_language") {
              this._render();
              return;
            }
          }
          if (areaId && this._shouldAutoMarkSectionDirty(section, fieldKey)) {
            this._markRoomSectionDraftDirty(areaId, section);
          }
        }

        const path = typeof event.composedPath === "function" ? event.composedPath() : [];
        const assetFieldHost = path.find((node) => {
          if (!(node instanceof Element)) return false;
          return String(node.getAttribute("data-field-key") || "") === "asset_groups";
        });
        if (assetFieldHost instanceof Element) {
          const areaId = String(assetFieldHost.getAttribute("data-area-id") || "");
          if (areaId) {
            this._markActiveFormDraftDirty(`room:${areaId}`);
            this._syncRoomAssetGroupDeviceOptions(areaId);
          }
        }

        const deviceFieldHost = path.find((node) => {
          if (!(node instanceof Element)) return false;
          return String(node.getAttribute("data-field-key") || "") === "device_groups";
        });
        if (deviceFieldHost instanceof Element) {
          const areaId = String(deviceFieldHost.getAttribute("data-area-id") || "");
          if (areaId) {
            this._markActiveFormDraftDirty(`room:${areaId}`);
            this._syncRoomDeviceGroupEntityOptions(areaId);
          }
        }
      });

      this.addEventListener("value-changed", (event) => {
        const target = event.target instanceof Element ? event.target : null;
        if (!target) return;

        const path = typeof event.composedPath === "function" ? event.composedPath() : [];
        const assetFieldHost = path.find((node) => {
          if (!(node instanceof Element)) return false;
          return String(node.getAttribute("data-field-key") || "") === "asset_groups";
        });
        const deviceFieldHost = path.find((node) => {
          if (!(node instanceof Element)) return false;
          return String(node.getAttribute("data-field-key") || "") === "device_groups";
        });
        const hostField = assetFieldHost instanceof Element
          ? assetFieldHost
          : (deviceFieldHost instanceof Element ? deviceFieldHost : null);
        const fallbackAreaId = target.getAttribute("data-area-id") || "";
        const fallbackFieldKey = target.getAttribute("data-field-key") || "";
        const areaId = hostField instanceof Element
          ? String(hostField.getAttribute("data-area-id") || "")
          : fallbackAreaId;
        const fieldKey = assetFieldHost instanceof Element
          ? "asset_groups"
          : (deviceFieldHost instanceof Element ? "device_groups" : fallbackFieldKey);
        if (areaId && fieldKey === "asset_groups") {
          this._markActiveFormDraftDirty(`room:${areaId}`);
          this._syncRoomAssetGroupDeviceOptions(areaId);
        }
        if (areaId && fieldKey === "device_groups") {
          this._markActiveFormDraftDirty(`room:${areaId}`);
          this._syncRoomDeviceGroupEntityOptions(areaId);
        }
      });

      this.addEventListener("focusin", (event) => {
        const target = event.target instanceof Element ? event.target : null;
        if (!target) return;

        if (this._isTrackedDataCaptureTarget(target)) {
          this._markActiveFormDraftDirty();
          return;
        }

        const fieldHost = target.closest("[data-field-key]");
        if (fieldHost && this._isTrackedDataCaptureTarget(fieldHost)) {
          this._markActiveFormDraftDirty();
        }
      });

      this.addEventListener("value-changed", (event) => {
        const target = event.target instanceof Element ? event.target : null;
        if (!target) return;

        if (this._isTrackedDataCaptureTarget(target)) {
          this._markActiveFormDraftDirty();
          const areaId = target.getAttribute("data-area-id") || "";
          const fieldKey = target.getAttribute("data-field-key") || "";
          const section = target.getAttribute("data-room-section") || this._roomSectionForFieldKey(target.getAttribute("data-field-key") || "");
          if (areaId && section === "persona" && fieldKey) {
            this._setRoomPersonaDraftField(areaId, fieldKey, this._readSelectControlValue(target));
            if (fieldKey === "tts_language") {
              this._render();
              return;
            }
          }
          if (areaId && this._shouldAutoMarkSectionDirty(section, fieldKey)) {
            this._markRoomSectionDraftDirty(areaId, section);
          }
          return;
        }

        const fieldHost = target.closest("[data-field-key]");
        if (fieldHost && this._isTrackedDataCaptureTarget(fieldHost)) {
          this._markActiveFormDraftDirty();
          const areaId = fieldHost.getAttribute("data-area-id") || "";
          const section = fieldHost.getAttribute("data-room-section") || this._roomSectionForFieldKey(fieldHost.getAttribute("data-field-key") || "");
          const fieldKey = fieldHost.getAttribute("data-field-key") || "";
          if (areaId && this._shouldAutoMarkSectionDirty(section, fieldKey)) {
            this._markRoomSectionDraftDirty(areaId, section);
          }
        }
      });

      this.addEventListener("selected", (event) => {
        const target = event.target instanceof Element ? event.target : null;
        if (!target || String(target.tagName || "").toUpperCase() !== "HA-SELECT") return;

        const detailValue = event?.detail && Object.prototype.hasOwnProperty.call(event.detail, "value")
          ? event.detail.value
          : undefined;
        const normalizedValue = detailValue === undefined || detailValue === null ? "" : String(detailValue);

        try {
          target.value = normalizedValue;
        } catch (err) {
          // no-op
        }

        if (!this._isTrackedDataCaptureTarget(target)) return;

        this._markActiveFormDraftDirty();
        const areaId = target.getAttribute("data-area-id") || "";
        const fieldKey = target.getAttribute("data-field-key") || "";
        const section = target.getAttribute("data-room-section") || this._roomSectionForFieldKey(fieldKey);

        if (areaId && section === "persona" && fieldKey) {
          this._setRoomPersonaDraftField(areaId, fieldKey, normalizedValue);
          if (fieldKey === "tts_language") {
            this._render();
            return;
          }
        }

        if (areaId && this._shouldAutoMarkSectionDirty(section, fieldKey)) {
          this._markRoomSectionDraftDirty(areaId, section);
        }
      });
    }

    // Refresh snapshot each time the panel is attached so integration option
    // changes from the gear dialog are reflected without requiring manual reload.
    if (this._hass && !this._loadingPromise) {
      this._loadingPromise = this._load().finally(() => {
        this._loadingPromise = null;
      });
    }

    if (!this._lifecycleListenersBound) {
      window.addEventListener("focus", this._onWindowFocus);
      document.addEventListener("visibilitychange", this._onVisibilityChange);
      this._lifecycleListenersBound = true;
    }
  }

  disconnectedCallback() {
    this._stopRoomVoicePreviewAudio();
    if (this._lifecycleListenersBound) {
      window.removeEventListener("focus", this._onWindowFocus);
      document.removeEventListener("visibilitychange", this._onVisibilityChange);
      this._lifecycleListenersBound = false;
    }
  }

  _ensureVoiceEnrollmentPersonView(personId) {
    if (!personId) return;
    this._selectedAreaId = null;
    this._selectedCompositeId = null;
    this._selectedPersonId = personId;
  }

  _hasActiveMergeDraft() {
    return Boolean(
      this._mergeMode && (
        String(this._mergeDraftName || "").trim() ||
        (Array.isArray(this._mergeDraftAreaIds) && this._mergeDraftAreaIds.length > 0)
      )
    );
  }

  _hasActiveEditMergeDraft() {
    return Boolean(this._editMergeCompositeId);
  }

  _currentFormDraftScope() {
    if (this._selectedPersonId) return `person:${this._selectedPersonId}`;
    if (this._selectedAreaId) return `room:${this._selectedAreaId}`;
    if (this._selectedCompositeId) return `composite:${this._selectedCompositeId}`;
    return "global";
  }

  _clearActiveFormDraft() {
    this._activeFormDraftScope = null;
    this._activeFormDraftDirty = false;
    this._updatePersonDraftActions();
  }

  _updatePersonDraftActions() {
    const personId = this._selectedPersonId || "";
    this.querySelectorAll("[data-person-actions]").forEach((container) => {
      const targetPersonId = container.getAttribute("data-person-id") || "";
      const isDirty = Boolean(
        personId
        && targetPersonId === personId
        && this._activeFormDraftDirty
        && this._activeFormDraftScope === `person:${personId}`
      );
      container.style.display = isDirty ? "flex" : "none";
    });
  }

  _roomSectionForFieldKey(fieldKey) {
    const roomDeviceFields = new Set([
      "device_groups",
      "voice_device_entity_ids",
      "media_player_entity_ids",
      "speaker_entity_ids",
      "light_entity_ids",
      "lamp_entity_ids",
      "shade_entity_ids",
      "tv_entity_ids",
      "room_sensor_entity_ids",
    ]);
    if (roomDeviceFields.has(fieldKey)) return "room_devices";

    const informationSourceFields = new Set([
      "ai_knowledge_enabled",
      "weather_source_entity_ids",
      "news_source_entity_ids",
      "asset_groups",
      "human_health_entity_ids",
      "room_health_entity_ids",
      "dashboard_entity_ids",
      "other_entity_ids",
      "environment_information_outputs",
    ]);
    if (informationSourceFields.has(fieldKey)) return "information_sources";

    return "";
  }

  _shouldAutoMarkSectionDirty(section, fieldKey) {
    if (section === "room_devices") {
      return fieldKey !== "device_groups";
    }
    if (section === "information_sources") {
      return fieldKey === "ai_knowledge_enabled";
    }
    return false;
  }

  _hasRoomSectionDraft(areaId, section) {
    const state = this._roomSectionDraftState?.[areaId];
    return Boolean(state && state[section]);
  }

  _hasAnyRoomSectionDraft() {
    const state = this._roomSectionDraftState || {};
    return Object.values(state).some((sections) => (
      Boolean(sections?.room_devices) || Boolean(sections?.information_sources)
    ));
  }

  _markRoomSectionDraftDirty(areaId, section) {
    if (!areaId || !section) return;
    const current = this._roomSectionDraftState[areaId] || {
      room_devices: false,
      information_sources: false,
    };
    if (!current[section]) {
      current[section] = true;
      this._roomSectionDraftState[areaId] = current;
    }
    this._updateRoomSectionDraftActions(areaId);
  }

  _clearRoomSectionDraft(areaId, section) {
    if (!areaId || !section) return;
    const current = this._roomSectionDraftState[areaId] || {
      room_devices: false,
      information_sources: false,
    };
    current[section] = false;
    this._roomSectionDraftState[areaId] = current;
    this._updateRoomSectionDraftActions(areaId);
  }

  _clearAllRoomSectionDrafts(areaId) {
    if (!areaId) return;
    this._roomSectionDraftState[areaId] = {
      room_devices: false,
      information_sources: false,
    };
    this._updateRoomSectionDraftActions(areaId);
  }

  _updateRoomSectionDraftActions(scopeId) {
    if (!scopeId) return;
    this.querySelectorAll(`[data-room-section-actions][data-area-id="${CSS.escape(scopeId)}"], [data-room-section-actions][data-composite-id="${CSS.escape(scopeId)}"]`).forEach((container) => {
      const section = container.getAttribute("data-room-section") || "";
      const id = container.getAttribute("data-area-id") || container.getAttribute("data-composite-id") || "";
      const isDirty = this._hasRoomSectionDraft(id, section);
      container.style.display = isDirty ? "flex" : "none";
    });
  }

  _markActiveFormDraftDirty(scope) {
    this._activeFormDraftScope = scope || this._currentFormDraftScope();
    this._activeFormDraftDirty = true;
    this._updatePersonDraftActions();
  }

  _setRoomPersonaDraftField(areaId, fieldKey, value) {
    if (!areaId || !fieldKey) return;
    const current = this._roomPersonaDraftState[areaId] || {};
    current[fieldKey] = value;
    this._roomPersonaDraftState[areaId] = current;
  }

  _roomPersonaDraftValue(areaId, fieldKey, fallback = "") {
    const current = this._roomPersonaDraftState?.[areaId];
    if (!current) return fallback;
    return current[fieldKey] !== undefined ? current[fieldKey] : fallback;
  }

  _clearRoomPersonaDraft(areaId) {
    if (!areaId) return;
    delete this._roomPersonaDraftState[areaId];
  }

  _hasActiveFormDraft() {
    if (this._hasAnyRoomSectionDraft()) {
      return true;
    }
    return Boolean(this._activeFormDraftDirty && this._activeFormDraftScope);
  }

  _isTrackedDataCaptureTarget(target) {
    if (!target || !(target instanceof Element)) return false;
    const tagName = String(target.tagName || "").toUpperCase();
    const isNativeControl = tagName === "INPUT" || tagName === "TEXTAREA" || tagName === "SELECT";
    const isHaControl = tagName.startsWith("HA-") && target.hasAttribute("data-field-key");
    if (!(isNativeControl || isHaControl)) return false;

    // Merge drafts are tracked separately and already preserve in-progress state.
    if (target.id === "cg-merge-name" || target.id === "cg-edit-merge-name") return false;
    if (target.classList.contains("cg-merge-room") || target.classList.contains("cg-edit-merge-room")) return false;

    return true;
  }

  _mergeLog(message, detail) {
    try {
      console.log(`[Concierge merge] ${message}`, detail);
    } catch (err) {
      // no-op
    }
  }

  _syncMergeDraftFromDom() {
    const mergeNameInput = this.querySelector("#cg-merge-name");
    if (mergeNameInput) {
      this._mergeDraftName = mergeNameInput.value || "";
    }

    return this._syncMergeSelectionFromDom();
  }

  _syncMergeSelectionFromDom() {
    const checkboxes = Array.from(this.querySelectorAll(".cg-merge-room"));
    const selectedAreaIds = checkboxes
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.value)
      .filter(Boolean);
    this._mergeDraftAreaIds = Array.from(new Set(selectedAreaIds));
    this._mergeLog("sync selection", {
      selectedAreaIds: [...this._mergeDraftAreaIds],
      checkedCount: this._mergeDraftAreaIds.length,
      checkboxSnapshot: checkboxes.map((checkbox) => ({
        value: checkbox.value,
        checked: checkbox.checked,
      })),
    });
    this._renderMergeStatus();
    return this._mergeDraftAreaIds;
  }

  _syncMergeSelectionForCheckbox(checkbox) {
    if (!checkbox || !checkbox.value) return;

    const nextSelection = new Set(this._mergeDraftAreaIds || []);
    if (checkbox.checked) {
      nextSelection.add(checkbox.value);
    } else {
      nextSelection.delete(checkbox.value);
    }

    this._mergeDraftAreaIds = Array.from(nextSelection);
    this._mergeLog("sync checkbox", {
      value: checkbox.value,
      checked: checkbox.checked,
      selectedAreaIds: [...this._mergeDraftAreaIds],
      count: this._mergeDraftAreaIds.length,
    });
    this._renderMergeStatus();
  }

  _openEditMergeDialog(compositeId) {
    const composite = this._composites[compositeId];
    if (!composite) return;

    this._editMergeCompositeId = compositeId;
    this._editMergeName = composite.name || compositeId;
    this._editMergeAreaIds = Array.from(new Set(Array.isArray(composite.area_ids) ? composite.area_ids : []));
    this._editMergeError = "";
    this._render();
  }

  _closeEditMergeDialog() {
    this._editMergeCompositeId = null;
    this._editMergeName = "";
    this._editMergeAreaIds = [];
    this._editMergeError = "";
    this._render();
  }

  _syncEditMergeSelectionFromDom() {
    const checkboxes = Array.from(this.querySelectorAll(".cg-edit-merge-room"));
    const selectedAreaIds = checkboxes
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.value)
      .filter(Boolean);
    this._editMergeAreaIds = Array.from(new Set(selectedAreaIds));
    return this._editMergeAreaIds;
  }

  async _saveEditMergeDialog() {
    const compositeId = this._editMergeCompositeId;
    if (!compositeId) return;

    const nameInput = this.querySelector("#cg-edit-merge-name");
    if (nameInput) {
      this._editMergeName = nameInput.value || "";
    }

    this._syncEditMergeSelectionFromDom();
    const selectedAreaIds = Array.from(new Set((this._editMergeAreaIds || []).filter(Boolean)));
    if (selectedAreaIds.length < 2) {
      this._editMergeError = "Select at least two rooms to keep the composite.";
      this._render();
      return;
    }

    if (!this._isSameFloorAreaSet(selectedAreaIds)) {
      this._editMergeError = "Selected rooms must be on the same floor.";
      this._render();
      return;
    }

    const composite = this._composites[compositeId] || {};
    const name = (this._editMergeName || composite.name || compositeId).trim();
    if (!name) {
      this._editMergeError = "Enter a composite name.";
      this._render();
      return;
    }

    this._editMergeError = "Updating composite...";
    this._render();

    try {
      await this._hass.callService(
        "concierge",
        "update_composite_config",
        {
          composite_id: compositeId,
          name,
          area_ids: selectedAreaIds,
        },
        undefined,
        true,
        true
      );
      this._composites[compositeId] = {
        ...composite,
        composite_id: compositeId,
        name,
        area_ids: selectedAreaIds,
      };
      this._closeEditMergeDialog();
      await this._load();
    } catch (err) {
      this._editMergeError = `Update failed: ${err?.message || err}`;
      this._render();
    }
  }

  _renderMergeStatus() {
    const status = this.querySelector(".cg-merge-status");
    if (!status) return;
    if (!this._mergeMode) {
      status.textContent = "";
      return;
    }
    const count = this._mergeDraftAreaIds.length;
    status.textContent = `${count} room${count === 1 ? "" : "s"} selected`;
    this._mergeLog("render status", { count, selectedAreaIds: [...this._mergeDraftAreaIds] });
  }

  set hass(hass) {
    this._hass = hass;
    this._maybeCheckPanelVersion();
    if (!this._loaded && !this._loadingPromise) {
      this._loadingPromise = this._load().finally(() => {
        this._loadingPromise = null;
      });
    }

    if (this._hasActiveVoiceEnrollmentDialog()) {
      return;
    }

    // Keep dialog state stable while editing global settings.
    if (this._globalSettingsDialogOpen) {
      return;
    }

    if (this._hasActiveFormDraft()) {
      return;
    }

    // If merge mode or the edit dialog has unsaved draft values, do not repaint from live updates.
    if (
      !this._selectedAreaId &&
      !this._selectedCompositeId &&
      (this._hasActiveMergeDraft() || this._hasActiveEditMergeDraft())
    ) {
      return;
    }

    this._render();
  }

  async _load() {
    const activeVoiceEnrollmentPersonId = this._voiceEnrollmentDialog?.personId || "";
    if (activeVoiceEnrollmentPersonId) {
      this._syncVoiceEnrollmentDialogOptionsFromDom(activeVoiceEnrollmentPersonId);
    } else {
      this._renderStartupLoading();
    }
    try {
      const snapshotResponse = await this._authFetch("/api/concierge/storage_snapshot", 12000);

      if (!snapshotResponse.ok) throw new Error(`HTTP ${snapshotResponse.status}`);
      const snapshot = await snapshotResponse.json();
      const areas = snapshot.areas || [];
      const floors = snapshot.floors || [];

      this._areas = Array.isArray(areas)
        ? areas.map((area) => ({
          ...area,
          id: area?.id || area?.area_id || area?.areaId || "",
        }))
        : [];
      this._floors = Array.isArray(floors)
        ? floors.map((floor) => {
          if (typeof floor === "string") {
            return { floor_id: floor, name: floor };
          }
          return {
            ...floor,
            floor_id: floor?.floor_id || floor?.id || "",
            name: floor?.name || floor?.floor_id || floor?.id || "Unassigned",
          };
        })
        : (floors && typeof floors === "object")
        ? Object.entries(floors).map(([floorId, floorName]) => ({
          floor_id: String(floorId || ""),
          name: String(floorName || floorId || "Unassigned"),
        }))
        : [];
      this._rooms = snapshot.rooms || {};
      this._composites = snapshot.composites || {};
      this._peopleRegistry = snapshot.people || {};
      this._people = snapshot.person_profiles || {};
      this._voiceProfiles = snapshot.voice_profiles || {};
      this._roomCatalog = snapshot.room_catalog || {};
      this._compositeCatalog = snapshot.composite_catalog || {};
      this._globalCatalog = snapshot.global_catalog || this._globalCatalog;
      this._globalFeatures = snapshot.global_features || {};
      this._globalContextUsage = snapshot.global_context_usage || {};
      await this._refreshLabelRegistry();
      const previousTtsProvider = String(this._integrationOptions?.tts_provider || "none");
      const incomingIntegrationOptions = snapshot.integration_options || {};
      this._integrationOptions = {
        ...this._integrationOptions,
        ...incomingIntegrationOptions,
        capabilities: {
          ...(this._integrationOptions?.capabilities || {}),
          ...(incomingIntegrationOptions?.capabilities || {}),
        },
      };
      const nextTtsProvider = String(this._integrationOptions?.tts_provider || "none");
      if (previousTtsProvider !== nextTtsProvider) {
        this._ttsCatalogLoaded = false;
        this._ttsCatalogLoadedAt = 0;
        this._ttsCatalogProvider = "";
        this._ttsCatalog = { provider: "none", defaultLanguage: "", languages: [], voicesByLanguage: {} };
      }
      this._ttsCatalog = this._normalizeTtsCatalog(snapshot.tts_catalog || {});
      this._ttsCatalogProvider = this._ttsCatalog.provider || nextTtsProvider;
      this._ttsCatalogLoaded = true;
      this._ttsCatalogLoadedAt = Date.now();
      this._archiveStatus = snapshot.archive_status || this._archiveStatus;
      this._assetIntelligenceConnected = Boolean(snapshot.asset_intelligence_connected);
      this._loadError = null;

      if (this._selectedAreaId && !this._areas.find((area) => area.id === this._selectedAreaId)) {
        this._goHome();
      }
      if (this._selectedCompositeId && !this._composites[this._selectedCompositeId]) {
        this._goHome();
      }
      const selectedPersonExists = Boolean(
        this._peopleRegistry?.[this._selectedPersonId]
        || this._people?.[this._selectedPersonId]
      );
      if (this._selectedPersonId && !selectedPersonExists) {
        this._goHome();
      }
    } catch (err) {
      this._loadError = err instanceof Error ? err.message : String(err);
    }
    this._loaded = true;
    this._render();
  }

  async _authFetch(url, timeoutMs = 0) {
    const token = this._hass?.auth?.data?.access_token;
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    if (!timeoutMs || timeoutMs <= 0) {
      return fetch(url, {
        method: "GET",
        credentials: "same-origin",
        headers,
      });
    }

    const controller = new AbortController();
    const timeoutHandle = setTimeout(() => controller.abort(), timeoutMs);
    try {
      return await fetch(url, {
        method: "GET",
        credentials: "same-origin",
        headers,
        signal: controller.signal,
      });
    } catch (err) {
      if (err?.name === "AbortError") {
        throw new Error(`Request timeout after ${timeoutMs}ms`);
      }
      throw err;
    } finally {
      clearTimeout(timeoutHandle);
    }
  }

  _maybeCheckPanelVersion(force = false) {
    const now = Date.now();

    if (!force && this._panelVersionCheckInFlight) {
      return this._panelVersionCheckInFlight;
    }

    if (!force && now - this._lastPanelVersionCheckAt < 60000) {
      return Promise.resolve(this._panelVersionStatus);
    }

    this._lastPanelVersionCheckAt = now;
    this._panelVersionCheckInFlight = this._checkPanelVersion().finally(() => {
      this._panelVersionCheckInFlight = null;
    });
    return this._panelVersionCheckInFlight;
  }

  async _checkPanelVersion() {
    const runningPanel = String(CONCIERGE_PANEL_BUILD?.selected_panel || "");
    const runningToken = String(CONCIERGE_PANEL_BUILD?.cache_token || "");

    if (!runningPanel || !runningToken) {
      return this._panelVersionStatus;
    }

    try {
      let payload = null;

      if (typeof this._hass?.callApi === "function") {
        payload = await this._hass.callApi("get", "concierge/panel_version");
      } else {
        const token = this._hass?.auth?.data?.access_token || "";
        const headers = {
          Accept: "application/json",
          "Cache-Control": "no-cache",
        };
        if (token) {
          headers.Authorization = `Bearer ${token}`;
        }

        const response = await fetch("/api/concierge/panel_version", {
          method: "GET",
          cache: "no-store",
          credentials: "same-origin",
          headers,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        payload = await response.json();
      }

      const latestPanel = String(payload?.selected_panel || "");
      const latestToken = String(payload?.cache_token || "");
      const stale = !!latestPanel && !!latestToken && (
        latestPanel !== runningPanel || latestToken !== runningToken
      );

      this._panelVersionStatus = {
        running_panel: runningPanel,
        running_token: runningToken,
        latest_panel: latestPanel,
        latest_token: latestToken,
        stale,
      };

      if (!stale) {
        this._panelVersionDismissed = false;
      }

      if (stale) {
        this._render();
      }
    } catch (err) {
      // no-op
    }

    return this._panelVersionStatus;
  }

  _renderPanelUpdateBanner() {
    if (!this._panelVersionStatus?.stale || this._panelVersionDismissed) {
      return "";
    }

    return `
      <div style="margin-bottom:16px; border:1px solid color-mix(in srgb, var(--warning-color, #f57c00) 55%, #fff 45%); background:color-mix(in srgb, var(--warning-color, #f57c00) 12%, var(--card-background-color) 88%); border-radius:12px; padding:12px;">
        <div style="font-weight:700; margin-bottom:6px;">A newer Concierge panel is available.</div>
        <div style="margin-bottom:10px; color:var(--secondary-text-color);">
          Home Assistant has a newer frontend bundle than the one currently open. Reload this page to avoid stale UI behavior after an update.
        </div>
        <div style="display:flex; gap:8px; align-items:center;">
          <button type="button" data-panel-reload style="border:0; border-radius:10px; padding:8px 12px; background:var(--primary-color); color:#fff; cursor:pointer; font-weight:600;">Reload panel</button>
          <button type="button" data-panel-dismiss style="border:1px solid var(--divider-color); border-radius:10px; padding:8px 12px; background:transparent; color:var(--primary-text-color); cursor:pointer; font-weight:600;">Dismiss</button>
        </div>
      </div>
    `;
  }

  _reloadPanelPage() {
    try {
      const url = new URL(window.location.href);
      url.searchParams.set("concierge_reload", String(Date.now()));
      window.location.replace(url.toString());
    } catch (err) {
      try {
        window.location.reload();
      } catch (reloadErr) {
        // no-op
      }
    }
  }

  _normalizeTtsCatalog(catalog) {
    const provider = String(catalog?.provider || "none").trim() || "none";
    const defaultLanguage = String(catalog?.default_language || catalog?.defaultLanguage || "").trim();
    const languages = Array.isArray(catalog?.languages)
      ? catalog.languages.map((item) => String(item || "").trim()).filter(Boolean)
      : [];
    const rawLanguageLabels = catalog?.language_labels || catalog?.languageLabels || {};
    const languageLabels = {};
    Object.entries(rawLanguageLabels || {}).forEach(([language, label]) => {
      const key = String(language || "").trim();
      if (!key) return;
      languageLabels[key] = String(label || language || "").trim() || key;
    });
    const rawVoices = catalog?.voices_by_language || catalog?.voicesByLanguage || {};
    const voicesByLanguage = {};
    Object.entries(rawVoices || {}).forEach(([language, rows]) => {
      const key = String(language || "").trim();
      if (!key || !Array.isArray(rows)) return;
      voicesByLanguage[key] = rows
        .map((row) => ({
          voice_id: String(row?.voice_id || row?.voiceId || "").trim(),
          voice_name: String(row?.voice_name || row?.voiceName || row?.voice_id || row?.voiceId || "").trim(),
        }))
        .filter((row) => row.voice_id);
    });
    return {
      provider,
      defaultLanguage,
      languages,
      languageLabels,
      voicesByLanguage,
    };
  }

  _canonicalLanguageTag(value) {
    return String(value || "").trim().replace(/_/g, "-").toLowerCase();
  }

  _resolveCatalogLanguageKey(value, fallback = "") {
    const candidate = String(value || "").trim();
    if (!candidate) return String(fallback || "").trim();

    const languages = Array.isArray(this._ttsCatalog?.languages) ? this._ttsCatalog.languages : [];
    if (languages.includes(candidate)) return candidate;

    const normalizedCandidate = this._canonicalLanguageTag(candidate);
    const match = languages.find((language) => this._canonicalLanguageTag(language) === normalizedCandidate);
    return match || String(fallback || candidate).trim();
  }

  _openRoom(areaId) {
    if (!areaId) return;
    this._clearActiveFormDraft();
    this._clearAllRoomSectionDrafts(areaId);
    this._clearRoomPersonaDraft(areaId);
    this._selectedCompositeId = null;
    this._selectedPersonId = null;
    this._selectedAreaId = areaId;
    this._ttsCatalogLoaded = false;
    this._ttsCatalogLoadedAt = 0;
    this._activityTimelineLoaded = false;
    this._activityTimeline = [];
    this._render();
  }

  _openComposite(compositeId) {
    if (!compositeId) return;
    this._clearActiveFormDraft();
    if (this._selectedAreaId) this._clearAllRoomSectionDrafts(this._selectedAreaId);
    this._selectedAreaId = null;
    this._selectedPersonId = null;
    this._selectedCompositeId = compositeId;
    this._render();
  }

  _openPerson(personId) {
    if (!personId) return;
    this._clearActiveFormDraft();
    if (this._selectedAreaId) this._clearAllRoomSectionDrafts(this._selectedAreaId);
    this._selectedAreaId = null;
    this._selectedCompositeId = null;
    this._selectedPersonId = personId;
    this._render();
  }

  _goHome() {
    this._clearActiveFormDraft();
    if (this._selectedAreaId) this._clearAllRoomSectionDrafts(this._selectedAreaId);
    if (this._selectedAreaId) this._clearRoomPersonaDraft(this._selectedAreaId);
    this._selectedAreaId = null;
    this._selectedCompositeId = null;
    this._selectedPersonId = null;
    this._activityTimelineLoaded = false;
    this._activityTimeline = [];
    this._render();
  }

  _slugify(text) {
    return String(text || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "")
      || "composite";
  }

  _isDarkTheme() {
    const themes = this._hass?.themes || {};
    const darkMode = this._hass?.selectedTheme?.dark;
    if (typeof darkMode === "boolean") return darkMode;
    return Boolean(themes.darkMode);
  }

  _logoSrc() {
    return this._isDarkTheme() ? "/concierge-brand/Icon_dark.png" : "/concierge-brand/Icon_light.png";
  }

  _humanizeEntityId(entityId) {
    if (!entityId || typeof entityId !== "string") return "Not set";
    const objectId = entityId.includes(".") ? entityId.split(".")[1] : entityId;
    return objectId
      .split("_")
      .filter(Boolean)
      .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
      .join(" ");
  }

  _friendlyEntityName(entityId) {
    if (!entityId) return "Not set";
    const stateObj = this._hass?.states?.[entityId];
    const friendly = stateObj?.attributes?.friendly_name || stateObj?.name;
    return friendly || this._humanizeEntityId(entityId);
  }

  _integrationNameFromEntityId(entityId) {
    if (!entityId || typeof entityId !== "string") return "Integration";
    const domain = entityId.includes(".") ? entityId.split(".", 1)[0] : "";
    if (!domain) return "Integration";
    return domain
      .split("_")
      .filter(Boolean)
      .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
      .join(" ");
  }

  _sourceInfoFromLabel(entityId, label) {
    const raw = String(label || "").trim();
    if (raw.includes(" - ")) {
      const [integration, ...rest] = raw.split(" - ");
      const name = rest.join(" - ").trim();
      if (integration.trim() && name) {
        return {
          name,
          integration: integration.trim(),
        };
      }
    }

    return {
      name: raw || this._friendlyEntityName(entityId) || entityId,
      integration: this._integrationNameFromEntityId(entityId),
    };
  }

  _sourceInfoFromRow(row) {
    const entityId = String(row?.entity_id || "").trim();
    const rawName = String(row?.name || "").trim();
    const integration = String(row?.integration || "").trim();
    const displayName = String(row?.display_name || "").trim();

    if (displayName) {
      const parsedDisplay = this._sourceInfoFromLabel(entityId, displayName);
      if (parsedDisplay?.name) {
        if (integration && !parsedDisplay.integration) {
          parsedDisplay.integration = integration;
        }
        return parsedDisplay;
      }
    }

    if (rawName.includes(" - ")) {
      const parsedName = this._sourceInfoFromLabel(entityId, rawName);
      if (parsedName?.name) {
        if (integration && !parsedName.integration) {
          parsedName.integration = integration;
        }
        return parsedName;
      }
    }

    let name = rawName || this._friendlyEntityName(entityId) || entityId;
    if (integration) {
      const prefix = `${integration} - `;
      if (name.toLowerCase().startsWith(prefix.toLowerCase())) {
        name = name.slice(prefix.length).trim() || name;
      }
      return { name, integration };
    }

    const parsedFriendly = this._sourceInfoFromLabel(entityId, name);
    if (parsedFriendly?.name) return parsedFriendly;

    return {
      name,
      integration: this._integrationNameFromEntityId(entityId),
    };
  }

  _normalizeSourceInfo(entityId, sourceInfo) {
    if (sourceInfo && typeof sourceInfo === "object") {
      const name = String(sourceInfo.name || "").trim() || this._friendlyEntityName(entityId) || entityId;
      const integration = String(sourceInfo.integration || "").trim() || this._integrationNameFromEntityId(entityId);
      return { name, integration };
    }

    return this._sourceInfoFromLabel(entityId, String(sourceInfo || ""));
  }

  _personImage(person) {
    const entityId = person?.entity_id;
    const stateObj = entityId ? this._hass?.states?.[entityId] : null;
    const fromSnapshot = person?.entity_picture || person?.entity_picture_local || person?.picture;
    const fromState = stateObj?.attributes?.entity_picture || stateObj?.attributes?.entity_picture_local;
    return fromSnapshot || fromState || "";
  }

  _escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  async _refreshLabelRegistry() {
    if (!this._hass?.connection) return;

    try {
      const labels = await this._hass.callWS({
        type: "config/label_registry/list",
      });
      this._labelRegistry = Array.isArray(labels) ? labels : [];
    } catch (err) {
      this._labelRegistry = [];
    }
  }

  _applyLabelRegistryToPickers(root = this) {
    const labels = Array.isArray(this._labelRegistry) ? this._labelRegistry : [];

    root.querySelectorAll("ha-labels-picker, ha-label-picker").forEach((picker) => {
      try { picker._labels = labels; } catch (e) {}
      try {
        if (typeof picker.requestUpdate === "function") picker.requestUpdate();
      } catch (e) {}
    });
  }

  _labelIdsFromValue(value) {
    if (value === undefined || value === null) return [];
    const rawValues = Array.isArray(value)
      ? value
      : value instanceof Set
      ? Array.from(value)
      : [value];
    return rawValues.map((item) => {
      if (item && typeof item === "object") {
        const labelId = item.label_id ?? item.labelId ?? item.id ?? item.value;
        return String(labelId || "").trim();
      }
      return String(item || "").trim();
    }).filter(Boolean);
  }

  _roomAssetCandidates(areaId) {
    const catalog = this._roomCatalog?.[areaId] || this._compositeCatalog?.[areaId] || {};
    return Array.isArray(catalog.asset_device_rows) ? catalog.asset_device_rows : [];
  }

  _assetGroupLabelIds(group) {
    if (!group || typeof group !== "object") return [];
    return this._labelIdsFromValue(group.label_ids || group.labels || []);
  }

  _assetGroupDeviceIds(group) {
    if (!group || typeof group !== "object") return [];
    return this._labelIdsFromValue(group.device_ids || group.asset_device_ids || []);
  }

  _roomAssetGroups(room) {
    return Array.isArray(room?.asset_groups) ? room.asset_groups : [];
  }

  _roomsForAreaIds(areaIds) {
    const ids = Array.isArray(areaIds) ? areaIds : [];
    return ids
      .map((areaId) => this._rooms?.[areaId])
      .filter((room) => Boolean(room));
  }

  _combinedFieldEntityIdsForAreaIds(areaIds, fieldKey) {
    return Array.from(
      new Set(
        this._roomsForAreaIds(areaIds)
          .flatMap((room) => (Array.isArray(room?.[fieldKey]) ? room[fieldKey] : []))
          .map((value) => String(value || "").trim())
          .filter(Boolean)
      )
    );
  }

  _combinedAssetGroupsForAreaIds(areaIds) {
    const grouped = new Map();
    this._roomsForAreaIds(areaIds).forEach((room) => {
      this._roomAssetGroups(room).forEach((group) => {
        const groupName = String(group?.group_name || "").trim();
        const key = groupName.toLowerCase();
        const deviceIds = this._assetGroupDeviceIds(group);
        const existing = grouped.get(key) || { group_name: groupName, device_ids: [] };
        existing.group_name = existing.group_name || groupName;
        existing.device_ids = Array.from(new Set([...existing.device_ids, ...deviceIds]));
        grouped.set(key, existing);
      });
    });
    return Array.from(grouped.values()).filter((group) => group.group_name || group.device_ids.length);
  }

  _combinedDeviceGroupsForAreaIds(areaIds) {
    const grouped = new Map();
    this._roomsForAreaIds(areaIds).forEach((room) => {
      const roomDeviceGroups = Array.isArray(room?.device_groups) ? room.device_groups : [];
      roomDeviceGroups.forEach((group) => {
        const groupName = String(group?.group_name || "").trim();
        const key = groupName.toLowerCase();
        const entityIds = this._roomDeviceGroupEntityIds(group);
        const existing = grouped.get(key) || { group_name: groupName, entity_ids: [] };
        existing.group_name = existing.group_name || groupName;
        existing.entity_ids = Array.from(new Set([...existing.entity_ids, ...entityIds]));
        grouped.set(key, existing);
      });
    });
    return Array.from(grouped.values()).filter((group) => group.group_name || group.entity_ids.length);
  }

  _compositeDeviceFieldPayload(compositeId, deviceGroups) {
    const catalog = this._compositeCatalog?.[compositeId] || {};
    const fieldKeys = [
      "voice_device_entity_ids",
      "media_player_entity_ids",
      "speaker_entity_ids",
      "light_entity_ids",
      "shade_entity_ids",
      "room_sensor_entity_ids",
    ];

    const fieldSets = new Map(
      fieldKeys.map((fieldKey) => {
        const ids = new Set(
          (Array.isArray(catalog[fieldKey]) ? catalog[fieldKey] : [])
            .map((row) => String(row?.entity_id || "").trim())
            .filter(Boolean)
        );
        return [fieldKey, ids];
      })
    );

    const payload = {
      voice_device_entity_ids: [],
      media_player_entity_ids: [],
      speaker_entity_ids: [],
      light_entity_ids: [],
      shade_entity_ids: [],
      room_sensor_entity_ids: [],
    };

    const entityIds = Array.from(
      new Set(
        (Array.isArray(deviceGroups) ? deviceGroups : [])
          .flatMap((group) => this._roomDeviceGroupEntityIds(group))
      )
    );

    entityIds.forEach((entityId) => {
      fieldKeys.forEach((fieldKey) => {
        if (fieldSets.get(fieldKey)?.has(entityId)) {
          payload[fieldKey].push(entityId);
        }
      });
    });

    return payload;
  }

  _assetGroupMatchesLabels(candidateRow, selectedLabelIds) {
    const candidateLabelIds = this._labelIdsFromValue(candidateRow?.label_ids || []);
    if (!selectedLabelIds.length) return true;
    return selectedLabelIds.some((labelId) => candidateLabelIds.includes(labelId));
  }

  _filteredRoomAssetCandidates(areaId, selectedLabelIds, blockedDeviceIds = []) {
    const blocked = new Set(this._labelIdsFromValue(blockedDeviceIds));
    return this._roomAssetCandidates(areaId).filter((row) => {
      const deviceId = String(row?.device_id || "").trim();
      if (!deviceId || blocked.has(deviceId)) return false;
      return this._assetGroupMatchesLabels(row, selectedLabelIds);
    });
  }

  _selectedIds(room, key) {
    const value = room?.[key];
    return Array.isArray(value) ? value : [];
  }

  _collectSelected(selectElement) {
    if (!selectElement) return [];
    return Array.from(selectElement.selectedOptions || []).map((item) => item.value).filter(Boolean);
  }

  _readSelectControlValue(selectElement) {
    if (!selectElement) return "";
    const tagName = String(selectElement.tagName || "").toUpperCase();
    if (tagName === "HA-SELECTOR") {
      return String(selectElement.value || "").trim();
    }
    if (tagName === "HA-ENTITY-PICKER") {
      const rawValue = selectElement.value;
      if (rawValue && typeof rawValue === "object") {
        const entityId = rawValue.entity_id || rawValue.entityId || rawValue.value || rawValue.id || "";
        return String(entityId || "").trim();
      }
      return String(rawValue || "").trim();
    }
    if (tagName === "HA-DEVICE-PICKER") {
      return String(selectElement.value || "").trim();
    }
    const selectedItem = selectElement.querySelector?.("ha-list-item[selected], mwc-list-item[selected]");
    if (selectedItem) {
      return String(selectedItem.value || selectedItem.getAttribute("value") || "").trim();
    }
    return String(selectElement.value || "").trim();
  }

  _readSelectControlLabel(selectElement) {
    if (!selectElement) return "";
    const tagName = String(selectElement.tagName || "").toUpperCase();
    if (tagName === "HA-SELECTOR") {
      try {
        const labelMap = JSON.parse(selectElement.getAttribute("data-label-map") || "{}");
        const value = String(selectElement.value || "").trim();
        return String(labelMap[value] || "").trim();
      } catch (err) {
        return "";
      }
    }
    if (tagName === "HA-ENTITY-PICKER") {
      const value = String(selectElement.value || "").trim();
      return this._friendlyEntityName(value);
    }
    if (tagName === "HA-DEVICE-PICKER") {
      const value = String(selectElement.value || "").trim();
      try {
        const labelMap = JSON.parse(selectElement.getAttribute("data-label-map") || "{}");
        return String(labelMap[value] || "").trim();
      } catch (err) {
        return "";
      }
    }
    const selectedItem = selectElement.querySelector?.("ha-list-item[selected], mwc-list-item[selected]");
    if (selectedItem) {
      return String(selectedItem.textContent || "").trim();
    }
    const selectedOption = selectElement.selectedOptions?.[0];
    return String(selectedOption?.textContent || "").trim();
  }

  _roomSourceSelectId(areaId, fieldKey) {
    return `cg-room-${areaId}-${fieldKey}`.replace(/[^a-zA-Z0-9_-]/g, "_");
  }

  _sourceValueMap(selectElement) {
    if (!selectElement) return {};
    try {
      return JSON.parse(selectElement.getAttribute("data-source-value-map") || "{}");
    } catch (err) {
      return {};
    }
  }

  _sourcePickerValueForEntityId(selectElement, entityId) {
    const targetEntityId = String(entityId || "").trim();
    if (!selectElement || !targetEntityId) return "";

    const valueMap = this._sourceValueMap(selectElement);
    const direct = Object.entries(valueMap).find(([, mappedEntityId]) => String(mappedEntityId || "").trim() === targetEntityId);
    if (direct) return String(direct[0] || "").trim();
    return targetEntityId;
  }

  _syncSourcePickerAvailability(selectElement, selectedEntityIds) {
    if (!selectElement) return;
    const selectedSet = new Set((Array.isArray(selectedEntityIds) ? selectedEntityIds : []).filter(Boolean).map((value) => String(value).trim()));
    const tagName = String(selectElement.tagName || "").toUpperCase();
    const valueMap = this._sourceValueMap(selectElement);

    if (tagName === "SELECT") {
      Array.from(selectElement.options || []).forEach((option) => {
        const value = String(option.value || "").trim();
        if (!value) {
          option.disabled = false;
          option.hidden = false;
          return;
        }
        const mappedEntityId = String(valueMap[value] || value).trim();
        const unavailable = selectedSet.has(mappedEntityId);
        option.disabled = unavailable;
        option.hidden = unavailable;
      });
      if (selectElement.value) {
        const currentEntityId = String(valueMap[selectElement.value] || selectElement.value || "").trim();
        if (selectedSet.has(currentEntityId)) {
          selectElement.value = "";
        }
      }
      return;
    }

    if (tagName === "HA-ENTITY-PICKER") {
      let allowed = [];
      try {
        allowed = JSON.parse(selectElement.getAttribute("data-all-entity-ids") || "[]");
      } catch (err) {
        allowed = [];
      }
      if (Array.isArray(allowed) && allowed.length) {
        const filtered = allowed.filter((entityId) => !selectedSet.has(String(entityId || "").trim()));
        selectElement.setAttribute("data-allowed-entity-ids", JSON.stringify(filtered));
      }
      const current = String(selectElement.value || "").trim();
      if (current) {
        const mappedEntityId = String(valueMap[current] || current).trim();
        if (selectedSet.has(mappedEntityId)) selectElement.value = "";
      }
      return;
    }

    if (tagName === "HA-DEVICE-PICKER") {
      let allDeviceIds = [];
      try {
        allDeviceIds = JSON.parse(selectElement.getAttribute("data-all-device-ids") || "[]");
      } catch (err) {
        allDeviceIds = [];
      }
      const blockedSourceValues = new Set(
        Array.from(selectedSet).map((entityId) => this._sourcePickerValueForEntityId(selectElement, entityId)).filter(Boolean)
      );
      if (Array.isArray(allDeviceIds) && allDeviceIds.length) {
        const filtered = allDeviceIds.filter((deviceId) => !blockedSourceValues.has(String(deviceId || "").trim()));
        selectElement.setAttribute("data-allowed-device-ids", JSON.stringify(filtered));
      }
      const current = String(selectElement.value || "").trim();
      if (current) {
        const mappedEntityId = String(valueMap[current] || current).trim();
        if (selectedSet.has(mappedEntityId)) selectElement.value = "";
      }
    }
  }

  _personIntentAbilityCatalog() {
    return [
      { value: "general_qna", label: "Allow General Q&A" },
      { value: "room_context_info", label: "Room Context Info" },
      { value: "household_help", label: "Household Help" },
      { value: "home_control", label: "Home Control" },
      { value: "media_control", label: "Media Control" },
      { value: "safety_alert", label: "Safety Alert" },
      { value: "status_summary", label: "Status Summary" },
    ];
  }

  _syncPersonIntentAbilityPicker(personId) {
    if (!personId) return;
    const picker = this.querySelector(`[data-person-id="${CSS.escape(personId)}"][data-field-key="minor_intent_ability_picker"]`);
    if (!picker) return;

    const selectedSet = new Set(
      Array.from(this.querySelectorAll(`.cg-person-intent-item[data-person-id="${CSS.escape(personId)}"]`))
        .map((item) => String(item.getAttribute("data-intent-class") || "").trim())
        .filter(Boolean)
    );

    const currentValue = String(picker.value || "").trim();
    const optionsMarkup = ["<option value=\"\">Select an intent ability</option>"]
      .concat(
        this._personIntentAbilityCatalog()
          .filter((item) => !selectedSet.has(item.value))
          .map((item) => `<option value="${this._escapeHtml(item.value)}">${this._escapeHtml(item.label)}</option>`)
      )
      .join("");

    picker.innerHTML = optionsMarkup;
    if (currentValue && !selectedSet.has(currentValue)) {
      picker.value = currentValue;
    }
  }

  _renderMultiSelect(areaId, fieldKey, title, options, selected) {
    const rows = Array.isArray(options) ? options : [];
    const selectedSet = new Set(Array.isArray(selected) ? selected : []);
    const optionsMarkup = rows.map((row) => {
      const entityId = row.entity_id || "";
      const label = row.name || this._friendlyEntityName(entityId) || entityId;
      const selectedAttr = selectedSet.has(entityId) ? " selected" : "";
      return `<option value="${this._escapeHtml(entityId)}"${selectedAttr}>${this._escapeHtml(label)}</option>`;
    }).join("");

    return `
      <div class="cg-field">
        <label>${this._escapeHtml(title)}</label>
        <select multiple class="cg-multi" data-area-id="${this._escapeHtml(areaId)}" data-field-key="${this._escapeHtml(fieldKey)}">
          ${optionsMarkup}
        </select>
      </div>
    `;
  }

  _renderCategorySelect(id, options, selectedEntityId, emptyLabel) {
    const rows = Array.isArray(options) ? options : [];
    if (!rows.length) {
      return `
        <select id="${this._escapeHtml(id)}" disabled>
          <option value="">${this._escapeHtml(emptyLabel)}</option>
        </select>
      `;
    }

    const optionsMarkup = [`<option value="">Not set</option>`]
      .concat(rows.map((row) => {
        const entityId = row.entity_id || "";
        const label = row.name || entityId;
        const selected = entityId === selectedEntityId ? " selected" : "";
        return `<option value="${this._escapeHtml(entityId)}"${selected}>${this._escapeHtml(label)}</option>`;
      }))
      .join("");
    return `<select id="${this._escapeHtml(id)}">${optionsMarkup}</select>`;
  }

  _collectGlobalSourceEntityIds(contextType) {
    if (!contextType) return [];

    return Array.from(this.querySelectorAll(`.cg-selected-source[data-context-type="${CSS.escape(contextType)}"]`))
      .map((row) => row.getAttribute("data-source-entity-id") || "")
      .filter(Boolean);
  }

  _collectRoomSourceEntityIds(areaId, fieldKey) {
    if (!areaId || !fieldKey) return [];

    return Array.from(this.querySelectorAll(`.cg-room-selected-item[data-area-id="${CSS.escape(areaId)}"][data-field-key="${CSS.escape(fieldKey)}"]`))
      .map((row) => row.getAttribute("data-source-entity-id") || "")
      .filter(Boolean);
  }

  _isRoomSourceReorderable(fieldKey) {
    return fieldKey === "weather_source_entity_ids" || fieldKey === "news_source_entity_ids";
  }

  _renderRoomSelectedSourceRow(areaId, fieldKey, entityId, sourceInfo, reorderable = false) {
    const normalized = this._normalizeSourceInfo(entityId, sourceInfo);
    return `
      <div
        class="cg-selected-source cg-room-selected-item"
        draggable="${reorderable ? "true" : "false"}"
        data-reorderable="${reorderable ? "true" : "false"}"
        data-area-id="${this._escapeHtml(areaId)}"
        data-field-key="${this._escapeHtml(fieldKey)}"
        data-source-entity-id="${this._escapeHtml(entityId)}">
        <div class="cg-selected-source-label">
          ${reorderable
    ? '<span class="cg-drag-handle" title="Drag to reorder" aria-label="Drag to reorder">::</span>'
    : ""}
          <div class="cg-selected-source-text">
            <div class="cg-selected-source-primary">${this._escapeHtml(normalized.name || entityId)}</div>
            <div class="cg-selected-source-secondary">${this._escapeHtml(normalized.integration || this._integrationNameFromEntityId(entityId))}</div>
          </div>
        </div>
        <ha-button class="cg-remove-source cg-room-remove-source" appearance="plain" aria-label="Remove source">Remove</ha-button>
      </div>
    `;
  }

  _syncRoomSelectedEmptyState(areaId, fieldKey) {
    if (!areaId || !fieldKey) return;

    const list = this.querySelector(`.cg-room-selected[data-area-id="${CSS.escape(areaId)}"][data-field-key="${CSS.escape(fieldKey)}"]`);
    if (!list) return;

    const empty = list.querySelector(".cg-selected-empty");
    const hasRows = Boolean(list.querySelector(".cg-room-selected-item"));
    if (empty) {
      empty.style.display = hasRows ? "none" : "block";
    }
  }

  _renderAssetGroupRow(areaId, group, index, readOnly = false) {
    const groupName = String(group?.group_name || "").trim();
    const deviceIds = this._assetGroupDeviceIds(group);
    const candidateById = new Map(
      this._roomAssetCandidates(areaId)
        .map((row) => [String(row?.device_id || "").trim(), row])
        .filter(([deviceId]) => Boolean(deviceId))
    );
    const deviceMarkup = deviceIds.length
      ? deviceIds.map((deviceId) => {
        const normalizedDeviceId = String(deviceId || "").trim();
        const row = candidateById.get(normalizedDeviceId);
        const label = String(row?.display_name || row?.name || normalizedDeviceId || "").trim();
        return `
          <div class="cg-selected-source cg-asset-group-device-row" data-device-id="${this._escapeHtml(normalizedDeviceId)}">
            <div class="cg-selected-source-label">
              <div class="cg-selected-source-text">
                <div class="cg-selected-source-primary">${this._escapeHtml(label)}</div>
              </div>
            </div>
            ${readOnly ? "" : `<ha-button class="cg-remove-source cg-asset-device-remove" appearance="plain" data-device-id="${this._escapeHtml(normalizedDeviceId)}" aria-label="Remove asset">Remove</ha-button>`}
          </div>
        `;
      }).join("")
      : `<span class="cg-muted">No devices selected</span>`;

    return `
      <div class="cg-asset-group-row" data-asset-group-index="${this._escapeHtml(String(index))}" data-group-name="${this._escapeHtml(groupName)}" data-device-ids="${this._escapeHtml(JSON.stringify(deviceIds))}">
        <div class="cg-asset-group-row-head" style="display:flex;align-items:flex-start;gap:12px;">
          <div>
            <div class="cg-asset-group-name" style="font-weight:600;">${this._escapeHtml(groupName || "Unnamed group")}</div>
          </div>
        </div>
        <div class="cg-asset-group-device-list">${deviceMarkup}</div>
      </div>
    `;
  }

  _roomDeviceGroupEntityIds(group) {
    return Array.from(
      new Set(
        (Array.isArray(group?.entity_ids) ? group.entity_ids : [])
          .map((entityId) => String(entityId || "").trim())
          .filter(Boolean)
      )
    );
  }

  _roomDeviceGroups(room) {
    const groups = Array.isArray(room?.device_groups) ? room.device_groups : [];
    return groups
      .map((group) => ({
        group_name: String(group?.group_name || "").trim(),
        entity_ids: this._roomDeviceGroupEntityIds(group),
      }))
      .filter((group) => group.group_name || group.entity_ids.length);
  }

  _roomDeviceCandidates(areaId) {
    const catalog = this._roomCatalog?.[areaId] || this._compositeCatalog?.[areaId] || {};
    const keys = [
      "voice_device_entity_ids",
      "media_player_entity_ids",
      "speaker_entity_ids",
      "light_entity_ids",
      "lamp_entity_ids",
      "shade_entity_ids",
      "tv_entity_ids",
      "room_sensor_entity_ids",
      "room_health_entity_ids",
      "human_health_entity_ids",
      "dashboard_entity_ids",
      "other_entity_ids",
    ];

    const byId = new Map();
    keys.forEach((key) => {
      const rows = Array.isArray(catalog[key]) ? catalog[key] : [];
      rows.forEach((row) => {
        const entityId = String(row?.entity_id || "").trim();
        if (!entityId || byId.has(entityId)) return;
        byId.set(entityId, {
          entity_id: entityId,
          name: String(row?.name || entityId).trim(),
          integration: String(row?.integration || "").trim(),
          display_name: String(row?.display_name || row?.name || entityId).trim(),
          label_ids: this._labelIdsFromValue(row?.label_ids || []),
        });
      });
    });

    return Array.from(byId.values()).sort((left, right) => {
      const leftLabel = String(left.display_name || left.name || left.entity_id || "");
      const rightLabel = String(right.display_name || right.name || right.entity_id || "");
      return leftLabel.localeCompare(rightLabel);
    });
  }

  _renderRoomDeviceGroupRow(areaId, group, index, readOnly = false) {
    const groupName = String(group?.group_name || "").trim();
    const entityIds = this._roomDeviceGroupEntityIds(group);
    const candidateById = new Map(
      this._roomDeviceCandidates(areaId)
        .map((row) => [String(row?.entity_id || "").trim(), row])
        .filter(([entityId]) => Boolean(entityId))
    );

    const entityMarkup = entityIds.length
      ? entityIds.map((entityId) => {
        const normalizedEntityId = String(entityId || "").trim();
        const row = candidateById.get(normalizedEntityId);
        const label = String(row?.display_name || row?.name || normalizedEntityId || "").trim();
        return `
          <div class="cg-selected-source cg-room-device-group-device-row" data-entity-id="${this._escapeHtml(normalizedEntityId)}">
            <div class="cg-selected-source-label">
              <div class="cg-selected-source-text">
                <div class="cg-selected-source-primary">${this._escapeHtml(label)}</div>
              </div>
            </div>
            ${readOnly ? "" : `<ha-button class="cg-remove-source cg-room-device-remove" appearance="plain" data-entity-id="${this._escapeHtml(normalizedEntityId)}" aria-label="Remove room device">Remove</ha-button>`}
          </div>
        `;
      }).join("")
      : `<span class="cg-muted">No devices selected</span>`;

    return `
      <div class="cg-device-group-row" data-device-group-index="${this._escapeHtml(String(index))}" data-group-name="${this._escapeHtml(groupName)}" data-entity-ids="${this._escapeHtml(JSON.stringify(entityIds))}">
        <div class="cg-asset-group-row-head" style="display:flex;align-items:flex-start;gap:12px;">
          <div>
            <div class="cg-asset-group-name" style="font-weight:600;">${this._escapeHtml(groupName || "Unnamed group")}</div>
          </div>
        </div>
        <div class="cg-asset-group-device-list">${entityMarkup}</div>
      </div>
    `;
  }

  _collectRoomDeviceGroups(areaId) {
    const list = this.querySelector(`.cg-device-groups[data-area-id="${CSS.escape(areaId)}"]`);
    if (!list) return [];

    return Array.from(list.querySelectorAll(".cg-device-group-row")).map((row) => {
      let entityIds = [];
      try { entityIds = JSON.parse(row.getAttribute("data-entity-ids") || "[]"); } catch (err) { entityIds = []; }
      return {
        group_name: String(row.getAttribute("data-group-name") || "").trim(),
        entity_ids: this._labelIdsFromValue(entityIds),
      };
    }).filter((group) => group.group_name || group.entity_ids.length);
  }

  _syncRoomDeviceGroupEntityOptions(areaId) {
    if (!areaId) return;

    const labelPicker = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="device_groups"][data-role="device-label-picker"]`);
    const entityPicker = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="device_groups"][data-role="device-entity-picker"]`);
    if (!entityPicker) {
      this._syncRoomDeviceGroupAddButtonState(areaId);
      return;
    }

    const selectedLabelIds = this._labelIdsFromValue(labelPicker?.value || labelPicker?.labelPicker?.value || []);
    const selectedLabelSet = new Set(selectedLabelIds);
    const blockedEntityIds = this._collectRoomDeviceGroups(areaId).flatMap((group) => this._roomDeviceGroupEntityIds(group));
    const blockedSet = new Set(blockedEntityIds);
    const candidates = this._roomDeviceCandidates(areaId).filter((row) => {
      const entityId = String(row?.entity_id || "").trim();
      if (!entityId || blockedSet.has(entityId)) return false;
      if (!selectedLabelSet.size) return true;
      const rowLabelIds = this._labelIdsFromValue(row?.label_ids || []);
      return rowLabelIds.some((labelId) => selectedLabelSet.has(labelId));
    });
    const allowedEntityIds = candidates.map((row) => String(row?.entity_id || "").trim()).filter(Boolean);
    const allowedSet = new Set(allowedEntityIds);

    try {
      entityPicker.setAttribute("data-allowed-entity-ids", JSON.stringify(allowedEntityIds));
      entityPicker.includeEntities = allowedEntityIds;
    } catch (err) {
      // no-op
    }

    try {
      entityPicker.entityFilter = (candidate) => {
        if (typeof candidate === "string") return allowedSet.has(candidate);
        if (candidate && typeof candidate === "object") {
          const entityId = String(candidate.entity_id || candidate.entityId || candidate?.stateObj?.entity_id || "").trim();
          return allowedSet.has(entityId);
        }
        return false;
      };
    } catch (err) {
      // no-op
    }

    const currentValue = String(entityPicker.value || "").trim();
    if (currentValue && !allowedSet.has(currentValue)) {
      try { entityPicker.value = ""; } catch (err) {}
    }

    if (typeof entityPicker.requestUpdate === "function") {
      try { entityPicker.requestUpdate(); } catch (err) {}
    }

    this._syncRoomDeviceGroupAddButtonState(areaId);
  }

  _syncRoomDeviceGroupAddButtonState(areaId) {
    if (!areaId) return;

    const nameInput = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="device_groups"][data-role="device-group-name"]`);
    const entityPicker = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="device_groups"][data-role="device-entity-picker"]`);
    const addButton = this.querySelector(`.cg-device-group-add[data-area-id="${CSS.escape(areaId)}"]`);
    if (!nameInput || !addButton) return;

    const hasName = Boolean(String(nameInput.value || "").trim());
    const hasEntity = Boolean(this._readSelectControlValue(entityPicker));
    const shouldEnable = hasName && hasEntity;

    if (shouldEnable) {
      addButton.removeAttribute("disabled");
    } else {
      addButton.setAttribute("disabled", "");
    }
  }

  _addRoomDeviceGroupFromDraft(areaId) {
    if (!areaId) return;

    const nameInput = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="device_groups"][data-role="device-group-name"]`);
    const entityPicker = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="device_groups"][data-role="device-entity-picker"]`);
    const groupList = this.querySelector(`.cg-device-groups[data-area-id="${CSS.escape(areaId)}"]`);
    if (!nameInput || !entityPicker || !groupList) return;

    const groupName = String(nameInput.value || "").trim();
    const entityId = this._readSelectControlValue(entityPicker);
    if (!groupName || !entityId) return;

    const existingRow = Array.from(groupList.querySelectorAll(".cg-device-group-row")).find((row) => {
      const existingName = String(row.getAttribute("data-group-name") || "").trim();
      return existingName.toLowerCase() === groupName.toLowerCase();
    });

    if (existingRow) {
      let existingEntityIds = [];
      try {
        existingEntityIds = JSON.parse(existingRow.getAttribute("data-entity-ids") || "[]");
      } catch (err) {
        existingEntityIds = [];
      }

      const mergedEntityIds = Array.from(
        new Set([
          ...this._labelIdsFromValue(existingEntityIds),
          entityId,
        ])
      );
      const rowIndex = Number(existingRow.getAttribute("data-device-group-index") || "0");
      existingRow.outerHTML = this._renderRoomDeviceGroupRow(
        areaId,
        { group_name: groupName, entity_ids: mergedEntityIds },
        Number.isFinite(rowIndex) ? rowIndex : 0
      );
    } else {
      const nextIndex = groupList.querySelectorAll(".cg-device-group-row").length;
      groupList.insertAdjacentHTML("beforeend", this._renderRoomDeviceGroupRow(areaId, { group_name: groupName, entity_ids: [entityId] }, nextIndex));
    }

    try { entityPicker.value = ""; } catch (err) {}
    this._markActiveFormDraftDirty(`room:${areaId}`);
    this._markRoomSectionDraftDirty(areaId, this._roomSectionForFieldKey("device_groups"));
    this._syncRoomDeviceGroupEntityOptions(areaId);
  }

  _removeRoomDeviceFromGroupRow(row, entityId) {
    if (!row || !entityId) return;

    const list = row.closest(".cg-device-groups");
    const areaId = list?.getAttribute("data-area-id") || "";
    const groupName = String(row.getAttribute("data-group-name") || "").trim();
    let entityIds = [];
    try {
      entityIds = JSON.parse(row.getAttribute("data-entity-ids") || "[]");
    } catch (err) {
      entityIds = [];
    }

    const remainingEntityIds = this._labelIdsFromValue(entityIds).filter((id) => id !== entityId);
    if (!remainingEntityIds.length) {
      row.remove();
    } else {
      const rowIndex = Number(row.getAttribute("data-device-group-index") || "0");
      row.outerHTML = this._renderRoomDeviceGroupRow(
        areaId,
        { group_name: groupName, entity_ids: remainingEntityIds },
        Number.isFinite(rowIndex) ? rowIndex : 0
      );
    }

    if (areaId) {
      this._markActiveFormDraftDirty(`room:${areaId}`);
      this._markRoomSectionDraftDirty(areaId, this._roomSectionForFieldKey("device_groups"));
      this._syncRoomDeviceGroupEntityOptions(areaId);
    }
  }

  _renderRoomDeviceGroupsEditor(areaId, currentGroups, emptyLabel) {
    const groups = Array.isArray(currentGroups) ? currentGroups : [];
    const groupMarkup = groups.length
      ? groups.map((group, index) => this._renderRoomDeviceGroupRow(areaId, group, index)).join("")
      : `<div class="cg-muted cg-device-groups-empty">${this._escapeHtml(emptyLabel)}</div>`;

    return `
      <div class="cg-asset-group-form">
        <div class="cg-field">
          <label>Labels</label>
          <ha-labels-picker data-area-id="${this._escapeHtml(areaId)}" data-field-key="device_groups" data-role="device-label-picker" data-room-section="room_devices"></ha-labels-picker>
        </div>
        <div class="cg-field">
          <label for="cg-device-group-name-${this._escapeHtml(areaId)}">what do you call these?</label>
          <input id="cg-device-group-name-${this._escapeHtml(areaId)}" type="text" data-area-id="${this._escapeHtml(areaId)}" data-field-key="device_groups" data-role="device-group-name" placeholder="Lighting, Voice, Comfort, Safety">
        </div>
        <div class="cg-field cg-asset-device-field">
          <label>Devices and Sensors</label>
          <ha-entity-picker data-area-id="${this._escapeHtml(areaId)}" data-field-key="device_groups" data-role="device-entity-picker" data-room-section="room_devices"></ha-entity-picker>
        </div>
        <div class="cg-asset-group-add-wrap">
          <ha-button class="cg-device-group-add" data-area-id="${this._escapeHtml(areaId)}" disabled>Add</ha-button>
        </div>
      </div>
      <div class="cg-device-groups" data-area-id="${this._escapeHtml(areaId)}" data-field-key="device_groups" data-room-section="room_devices">
        ${groupMarkup}
      </div>
    `;
  }

  _renderCompositeDeviceGroupsReadOnly(compositeId, groups, emptyLabel) {
    const markup = Array.isArray(groups) && groups.length
      ? groups.map((group, index) => this._renderRoomDeviceGroupRow(compositeId, group, index, true)).join("")
      : `<div class="cg-muted">${this._escapeHtml(emptyLabel)}</div>`;
    return `<div class="cg-device-groups" data-area-id="${this._escapeHtml(compositeId)}">${markup}</div>`;
  }

  _renderCompositeAssetGroupsReadOnly(compositeId, groups, emptyLabel) {
    const markup = Array.isArray(groups) && groups.length
      ? groups.map((group, index) => this._renderAssetGroupRow(compositeId, group, index, true)).join("")
      : `<div class="cg-muted">${this._escapeHtml(emptyLabel)}</div>`;
    return `<div class="cg-asset-groups" data-area-id="${this._escapeHtml(compositeId)}">${markup}</div>`;
  }

  _collectRoomAssetGroups(areaId) {
    const list = this.querySelector(`.cg-asset-groups[data-area-id="${CSS.escape(areaId)}"]`);
    if (!list) return [];

    return Array.from(list.querySelectorAll(".cg-asset-group-row")).map((row) => {
      let deviceIds = [];
      try {
        deviceIds = JSON.parse(row.getAttribute("data-device-ids") || "[]");
      } catch (err) {
        deviceIds = [];
      }
      return {
        group_name: String(row.getAttribute("data-group-name") || "").trim(),
        device_ids: this._labelIdsFromValue(deviceIds),
      };
    }).filter((group) => group.group_name || group.device_ids.length);
  }

  _syncRoomAssetGroupDeviceOptions(areaId) {
    if (!areaId) return;

    const labelPicker = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="asset_groups"][data-role="asset-label-picker"]`);
    const entityPicker = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="asset_groups"][data-role="asset-entity-picker"]`);
    if (!entityPicker) {
      this._syncRoomAssetGroupAddButtonState(areaId);
      return;
    }

    const selectedLabelIds = this._labelIdsFromValue(labelPicker?.value || labelPicker?.labelPicker?.value || []);
    const selectedLabelSet = new Set(selectedLabelIds);
    const blockedDeviceIds = this._collectRoomAssetGroups(areaId).flatMap((group) => this._assetGroupDeviceIds(group));
    const candidates = this._filteredRoomAssetCandidates(areaId, selectedLabelIds, blockedDeviceIds);
    const allowedEntityIds = candidates.map((row) => String(row?.entity_id || "").trim()).filter(Boolean);
    const allowedSet = new Set(allowedEntityIds);

    try {
      entityPicker.setAttribute("data-allowed-entity-ids", JSON.stringify(allowedEntityIds));
      entityPicker.includeEntities = allowedEntityIds;
    } catch (err) {
      // no-op
    }

    try {
      entityPicker.entityFilter = (candidate) => {
        if (typeof candidate === "string") return allowedSet.has(candidate);
        if (candidate && typeof candidate === "object") {
          const entityId = String(candidate.entity_id || candidate.entityId || candidate?.stateObj?.entity_id || "").trim();
          if (!entityId || !allowedSet.has(entityId)) return false;
          if (!selectedLabelSet.size) return true;
          const row = candidates.find((item) => String(item?.entity_id || "").trim() === entityId);
          const rowLabelIds = this._labelIdsFromValue(row?.label_ids || []);
          return rowLabelIds.some((labelId) => selectedLabelSet.has(labelId));
        }
        return false;
      };
    } catch (err) {
      // no-op
    }

    const currentValue = String(entityPicker.value || "").trim();
    if (currentValue && !allowedSet.has(currentValue)) {
      try { entityPicker.value = ""; } catch (err) {}
    }

    if (typeof entityPicker.requestUpdate === "function") {
      try { entityPicker.requestUpdate(); } catch (err) {}
    }

    this._syncRoomAssetGroupAddButtonState(areaId);
  }

  _syncRoomAssetGroupAddButtonState(areaId) {
    if (!areaId) return;

    const nameInput = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="asset_groups"][data-role="asset-group-name"]`);
    const entityPicker = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="asset_groups"][data-role="asset-entity-picker"]`);
    const addButton = this.querySelector(`.cg-asset-group-add[data-area-id="${CSS.escape(areaId)}"]`);
    if (!nameInput || !addButton) return;

    const hasName = Boolean(String(nameInput.value || "").trim());
    const hasAsset = Boolean(this._readSelectControlValue(entityPicker));
    const shouldEnable = hasName && hasAsset;

    if (shouldEnable) {
      addButton.removeAttribute("disabled");
    } else {
      addButton.setAttribute("disabled", "");
    }
  }

  _addAssetGroupFromDraft(areaId) {
    if (!areaId) return;

    const nameInput = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="asset_groups"][data-role="asset-group-name"]`);
    const entityPicker = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="asset_groups"][data-role="asset-entity-picker"]`);
    const groupList = this.querySelector(`.cg-asset-groups[data-area-id="${CSS.escape(areaId)}"]`);
    if (!nameInput || !entityPicker || !groupList) return;

    const groupName = String(nameInput.value || "").trim();
    const entityId = this._readSelectControlValue(entityPicker);
    const selectedRow = this._roomAssetCandidates(areaId).find((row) => String(row?.entity_id || "").trim() === entityId);
    const deviceId = String(selectedRow?.device_id || "").trim();
    if (!groupName || !entityId || !deviceId) return;

    const existingRow = Array.from(groupList.querySelectorAll(".cg-asset-group-row")).find((row) => {
      const existingName = String(row.getAttribute("data-group-name") || "").trim();
      return existingName.toLowerCase() === groupName.toLowerCase();
    });

    if (existingRow) {
      let existingDeviceIds = [];
      try {
        existingDeviceIds = JSON.parse(existingRow.getAttribute("data-device-ids") || "[]");
      } catch (err) {
        existingDeviceIds = [];
      }

      const mergedDeviceIds = Array.from(
        new Set([
          ...this._labelIdsFromValue(existingDeviceIds),
          deviceId,
        ])
      );
      const rowIndex = Number(existingRow.getAttribute("data-asset-group-index") || "0");
      existingRow.outerHTML = this._renderAssetGroupRow(
        areaId,
        { group_name: groupName, device_ids: mergedDeviceIds },
        Number.isFinite(rowIndex) ? rowIndex : 0
      );
    } else {
      const nextIndex = groupList.querySelectorAll(".cg-asset-group-row").length;
      groupList.insertAdjacentHTML("beforeend", this._renderAssetGroupRow(areaId, { group_name: groupName, device_ids: [deviceId] }, nextIndex));
    }

    try { entityPicker.value = ""; } catch (err) {}
    this._markActiveFormDraftDirty(`room:${areaId}`);
    this._markRoomSectionDraftDirty(areaId, this._roomSectionForFieldKey("asset_groups"));
    this._syncRoomAssetGroupDeviceOptions(areaId);
    this._syncRoomSelectedEmptyState(areaId, "asset_groups");
  }

  _removeAssetGroupRow(row) {
    const list = row?.closest?.(".cg-asset-groups");
    const areaId = list?.getAttribute("data-area-id") || "";
    row?.remove?.();
    if (areaId) {
      this._markActiveFormDraftDirty(`room:${areaId}`);
      this._markRoomSectionDraftDirty(areaId, this._roomSectionForFieldKey("asset_groups"));
      this._syncRoomAssetGroupDeviceOptions(areaId);
    }
  }

  _removeAssetDeviceFromGroupRow(row, deviceId) {
    if (!row || !deviceId) return;

    const list = row.closest(".cg-asset-groups");
    const areaId = list?.getAttribute("data-area-id") || "";
    const groupName = String(row.getAttribute("data-group-name") || "").trim();
    let deviceIds = [];
    try {
      deviceIds = JSON.parse(row.getAttribute("data-device-ids") || "[]");
    } catch (err) {
      deviceIds = [];
    }

    const remainingDeviceIds = this._labelIdsFromValue(deviceIds).filter((id) => id !== deviceId);
    if (!remainingDeviceIds.length) {
      row.remove();
    } else {
      const rowIndex = Number(row.getAttribute("data-asset-group-index") || "0");
      row.outerHTML = this._renderAssetGroupRow(
        areaId,
        { group_name: groupName, device_ids: remainingDeviceIds },
        Number.isFinite(rowIndex) ? rowIndex : 0
      );
    }

    if (areaId) {
      this._markActiveFormDraftDirty(`room:${areaId}`);
      this._markRoomSectionDraftDirty(areaId, this._roomSectionForFieldKey("asset_groups"));
      this._syncRoomAssetGroupDeviceOptions(areaId);
    }
  }

  _renderRoomAssetGroupsEditor(areaId, title, options, currentGroups, emptyLabel) {
    const rows = Array.isArray(options) ? options : [];
    const groups = Array.isArray(currentGroups) ? currentGroups : [];
    const groupMarkup = groups.length
      ? groups.map((group, index) => this._renderAssetGroupRow(areaId, group, index)).join("")
      : `<div class="cg-muted cg-asset-groups-empty">${this._escapeHtml(emptyLabel)}</div>`;

    return `
      <div class="cg-config-card cg-asset-groups-card">
        <div class="cg-config-title">${this._escapeHtml(title)}</div>
        <div class="cg-asset-group-form">
          <div class="cg-field">
            <label>Labels</label>
            <ha-labels-picker data-area-id="${this._escapeHtml(areaId)}" data-field-key="asset_groups" data-role="asset-label-picker"></ha-labels-picker>
          </div>
          <div class="cg-field">
            <label for="cg-asset-group-name-${this._escapeHtml(areaId)}">what do you call these?</label>
            <input id="cg-asset-group-name-${this._escapeHtml(areaId)}" type="text" data-area-id="${this._escapeHtml(areaId)}" data-field-key="asset_groups" data-role="asset-group-name" placeholder="Artwork, Antiques, Electronics">
          </div>
          <div class="cg-field cg-asset-device-field">
            <label>Devices</label>
            <ha-entity-picker data-area-id="${this._escapeHtml(areaId)}" data-field-key="asset_groups" data-role="asset-entity-picker" data-room-section="information_sources"></ha-entity-picker>
          </div>
          <div class="cg-asset-group-add-wrap">
            <ha-button class="cg-asset-group-add" data-area-id="${this._escapeHtml(areaId)}" disabled>Add</ha-button>
          </div>
        </div>
        <div class="cg-asset-groups" data-area-id="${this._escapeHtml(areaId)}" data-field-key="asset_groups">
          ${groupMarkup}
        </div>
      </div>
    `;
  }

  _renderRoomSourceEditor(areaId, fieldKey, title, options, selectedEntityIds, emptyLabel, wrapInCard = true, titleNote = "") {
    const rows = Array.isArray(options) ? options : [];
    const selectedIds = Array.from(new Set(Array.isArray(selectedEntityIds) ? selectedEntityIds.filter(Boolean) : []));
    const reorderable = this._isRoomSourceReorderable(fieldKey);
    const roomSection = this._roomSectionForFieldKey(fieldKey);
    const byId = new Map(
      rows
        .map((row) => [row?.entity_id || "", this._sourceInfoFromRow(row)])
        .filter(([id]) => Boolean(id))
    );
    const selectId = this._roomSourceSelectId(areaId, fieldKey);
    const forceNativeSelect = fieldKey === "weather_source_entity_ids" || fieldKey === "news_source_entity_ids";
    const isEntityPicker = !forceNativeSelect && rows.length > 0 && rows.every((row) => String(row?.entity_id || "").includes("."));
    const availableRows = rows.filter((row) => !selectedIds.includes(String(row?.entity_id || "").trim()));
    const allowedEntityIdsJson = JSON.stringify(availableRows.map((row) => String(row?.entity_id || "").trim()).filter(Boolean));
    const allEntityIdsJson = JSON.stringify(rows.map((row) => String(row?.entity_id || "").trim()).filter(Boolean));
    const allowedDeviceIdsJson = JSON.stringify(availableRows.map((row) => String(row?.device_id || "").trim()).filter(Boolean));
    const sourceValueMapJson = JSON.stringify(
      rows.reduce((acc, row) => {
        const entityId = String(row?.entity_id || "").trim();
        const sourceValue = entityId;
        if (!sourceValue || !entityId) return acc;
        if (!acc[sourceValue]) {
          acc[sourceValue] = entityId;
        }
        return acc;
      }, {})
    );
    const labelMapJson = JSON.stringify(
      rows.reduce((acc, row) => {
        const sourceValue = String(row?.entity_id || "").trim();
        const label = String(row?.display_name || row?.name || row?.entity_id || "").trim();
        if (!sourceValue || !label) return acc;
        if (!acc[sourceValue]) {
          acc[sourceValue] = label;
        }
        return acc;
      }, {})
    );
    const sourceDetailsMapJson = JSON.stringify(
      rows.reduce((acc, row) => {
        const sourceValue = String(row?.entity_id || "").trim();
        if (!sourceValue) return acc;
        acc[sourceValue] = this._sourceInfoFromRow(row);
        return acc;
      }, {})
    );

    const selectMarkup = isEntityPicker
      ? `
          <ha-entity-picker
            id="${this._escapeHtml(selectId)}"
            data-area-id="${this._escapeHtml(areaId)}"
            data-field-key="${this._escapeHtml(fieldKey)}"
            data-room-section="${this._escapeHtml(roomSection)}"
            data-allowed-entity-ids="${this._escapeHtml(allowedEntityIdsJson)}"
            data-all-entity-ids="${this._escapeHtml(allEntityIdsJson)}"
            data-source-value-map="${this._escapeHtml(sourceValueMapJson)}"
            data-label-map="${this._escapeHtml(labelMapJson)}"
            data-source-details-map="${this._escapeHtml(sourceDetailsMapJson)}"
          ></ha-entity-picker>
        `
      : rows.length
      ? `
          <select
            id="${this._escapeHtml(selectId)}"
            data-area-id="${this._escapeHtml(areaId)}"
            data-field-key="${this._escapeHtml(fieldKey)}"
            data-room-section="${this._escapeHtml(roomSection)}"
            data-source-details-map="${this._escapeHtml(sourceDetailsMapJson)}"
            class="cg-room-source-select"
          >
            <option value="">Select a source to add</option>
            ${rows.map((row) => {
              const entityId = row?.entity_id || "";
              const label = String(row?.display_name || row?.name || entityId);
              const unavailable = selectedIds.includes(String(entityId || "").trim());
              return `<option value="${this._escapeHtml(entityId)}"${unavailable ? " disabled hidden" : ""}>${this._escapeHtml(label)}</option>`;
            }).join("")}
          </select>
        `
      : `
          <select
            id="${this._escapeHtml(selectId)}"
            data-area-id="${this._escapeHtml(areaId)}"
            data-field-key="${this._escapeHtml(fieldKey)}"
            data-room-section="${this._escapeHtml(roomSection)}"
            data-source-details-map="${this._escapeHtml(sourceDetailsMapJson)}"
            class="cg-room-source-select"
            disabled
          >
            <option value="">${this._escapeHtml(emptyLabel)}</option>
          </select>
        `;

    const selectedMarkup = selectedIds
      .map((entityId) => this._renderRoomSelectedSourceRow(areaId, fieldKey, entityId, byId.get(entityId) || entityId, reorderable))
      .join("");

    const content = `
      <div class="cg-config-title">${this._escapeHtml(title)}${titleNote ? ` <span class="cg-config-title-note">${this._escapeHtml(titleNote)}</span>` : ""}</div>
      <div class="cg-source-picker-row">
        ${selectMarkup}
        <ha-button
          class="cg-add-source cg-room-add-source"
          data-area-id="${this._escapeHtml(areaId)}"
          data-field-key="${this._escapeHtml(fieldKey)}"
          data-source-select-id="${this._escapeHtml(selectId)}"
          data-room-section="${this._escapeHtml(roomSection)}"
          ${rows.length ? "" : "disabled"}
        >Add</ha-button>
      </div>
      <div class="cg-selected-sources cg-source-selection-list cg-room-selected" data-area-id="${this._escapeHtml(areaId)}" data-field-key="${this._escapeHtml(fieldKey)}" data-room-section="${this._escapeHtml(roomSection)}">
        <div class="cg-selected-empty"${selectedMarkup ? ' style="display:none;"' : ""}>No sources selected</div>
        ${selectedMarkup}
      </div>
    `;

    if (!wrapInCard) {
      return `<div class="cg-inline-editor">${content}</div>`;
    }

    return `<div class="cg-config-card">${content}</div>`;
  }

  _renderSelectedSourceRow(contextType, entityId, label) {
    const normalized = this._normalizeSourceInfo(entityId, label);
    return `
      <div class="cg-selected-source" data-context-type="${this._escapeHtml(contextType)}" data-source-entity-id="${this._escapeHtml(entityId)}">
        <div class="cg-selected-source-label">
          <div class="cg-selected-source-text">
            <div class="cg-selected-source-primary">${this._escapeHtml(normalized.name || entityId)}</div>
            <div class="cg-selected-source-secondary">${this._escapeHtml(normalized.integration || this._integrationNameFromEntityId(entityId))}</div>
          </div>
        </div>
        <ha-button class="cg-remove-source" appearance="plain" aria-label="Remove source">Remove</ha-button>
      </div>
    `;
  }

  _syncSelectedSourceEmptyState(contextType) {
    if (!contextType) return;

    const list = this.querySelector(`.cg-selected-sources[data-context-type="${CSS.escape(contextType)}"]`);
    if (!list) return;

    const empty = list.querySelector(".cg-selected-empty");
    const hasRows = Boolean(list.querySelector(".cg-selected-source"));
    if (empty) {
      empty.style.display = hasRows ? "none" : "block";
    }
  }

  _renderGlobalSourceEditor(contextType, title, options, selectedEntityIds, emptyCatalogLabel) {
    const rows = Array.isArray(options) ? options : [];
    const selectedIds = Array.from(new Set(Array.isArray(selectedEntityIds) ? selectedEntityIds.filter(Boolean) : []));

    const globalSourceLabel = (row) => {
      if (!row || typeof row !== "object") return "";
      const displayName = String(row.display_name || "").trim();
      if (displayName) return displayName;

      const integration = String(row.integration || "").trim();
      const name = String(row.name || row.entity_id || "").trim();
      if (integration && name) return `${integration} - ${name}`;
      return name;
    };

    const byId = new Map(
      rows
        .map((row) => [row?.entity_id || "", this._sourceInfoFromRow(row)])
        .filter(([id]) => Boolean(id))
    );
    const sourceDetailsMapJson = JSON.stringify(
      rows.reduce((acc, row) => {
        const entityId = String(row?.entity_id || "").trim();
        if (!entityId) return acc;
        acc[entityId] = this._sourceInfoFromRow(row);
        return acc;
      }, {})
    );
    const selectId = `cg-${contextType}-source-select`;

    const selectMarkup = rows.length
      ? `
          <select id="${this._escapeHtml(selectId)}" data-source-details-map="${this._escapeHtml(sourceDetailsMapJson)}">
            <option value="">Select a source to add</option>
            ${rows.map((row) => {
              const entityId = row?.entity_id || "";
              const label = globalSourceLabel(row) || entityId;
              const unavailable = selectedIds.includes(String(entityId || "").trim());
              return `<option value="${this._escapeHtml(entityId)}"${unavailable ? " disabled hidden" : ""}>${this._escapeHtml(label)}</option>`;
            }).join("")}
          </select>
        `
      : `
          <select id="${this._escapeHtml(selectId)}" data-source-details-map="${this._escapeHtml(sourceDetailsMapJson)}" disabled>
            <option value="">${this._escapeHtml(emptyCatalogLabel)}</option>
          </select>
        `;

    const selectedMarkup = selectedIds
      .map((entityId) => {
        const sourceInfo = byId.get(entityId) || entityId;
        return this._renderSelectedSourceRow(contextType, entityId, sourceInfo);
      })
      .join("");

    return `
      <div class="cg-global-item">
        <label for="${this._escapeHtml(selectId)}">${this._escapeHtml(title)}</label>
        <div class="cg-source-picker-row">
          ${selectMarkup}
          <ha-button
            class="cg-add-source"
            data-context-type="${this._escapeHtml(contextType)}"
            data-source-select-id="${this._escapeHtml(selectId)}"
            ${rows.length ? "" : "disabled"}
          >Add</ha-button>
        </div>
        <div class="cg-selected-sources cg-source-selection-list" data-context-type="${this._escapeHtml(contextType)}">
          <div class="cg-selected-empty"${selectedMarkup ? ' style="display:none;"' : ""}>No sources selected</div>
          ${selectedMarkup}
        </div>
      </div>
    `;
  }

  _mergedGlobalConfig(key) {
    return this._globalFeatures[key] || this._globalContextUsage[key] || { enabled: false, options: {} };
  }

  _globalSourceRowsForContext(contextType) {
    const catalogKey = contextType === "weather" ? "weather_entity_ids" : "news_entity_ids";
    const catalogRows = Array.isArray(this._globalCatalog?.[catalogKey]) ? this._globalCatalog[catalogKey] : [];
    const byId = new Map(
      catalogRows
        .map((row) => [String(row?.entity_id || "").trim(), row])
        .filter(([entityId]) => Boolean(entityId))
    );

    const mergedConfig = this._mergedGlobalConfig(contextType);
    const selectedIds = Array.isArray(mergedConfig?.options?.source_entity_ids)
      ? mergedConfig.options.source_entity_ids.map((value) => String(value || "").trim()).filter(Boolean)
      : [];

    selectedIds.forEach((entityId) => {
      if (byId.has(entityId)) return;
      const friendlyName = this._friendlyEntityName(entityId) || entityId;
      byId.set(entityId, {
        entity_id: entityId,
        name: friendlyName,
        display_name: friendlyName,
        domain: entityId.includes(".") ? entityId.split(".", 1)[0] : "provider",
        integration: this._integrationNameFromEntityId(entityId),
      });
    });

    return Array.from(byId.values()).sort((left, right) => String(left?.display_name || left?.name || "").localeCompare(String(right?.display_name || right?.name || "")));
  }

  _activityFilterLabel(filterKey) {
    const labels = {
      all: "All",
      voice: "Voice",
      mobile: "Mobile",
      automation: "Automation",
      other: "Other",
    };
    return labels[filterKey] || "All";
  }

  _activityMatchesFilter(activity, filterKey) {
    if (!activity || filterKey === "all") return true;

    const channel = String(activity.channel || "").toLowerCase();
    if (filterKey === "voice") {
      return channel.includes("voice") || channel.includes("assist") || channel.includes("conversation");
    }
    if (filterKey === "mobile") {
      return channel.includes("mobile") || channel.includes("app") || channel.includes("push");
    }
    if (filterKey === "automation") {
      return channel.includes("automation") || channel.includes("script") || channel.includes("scene") || channel.includes("service");
    }
    if (filterKey === "other") {
      return !this._activityMatchesFilter(activity, "voice")
        && !this._activityMatchesFilter(activity, "mobile")
        && !this._activityMatchesFilter(activity, "automation");
    }
    return true;
  }

  _activityMatchesSearch(activity, searchTerm) {
    const term = String(searchTerm || "").trim().toLowerCase();
    if (!term) return true;

    const blob = [
      activity?.started_at,
      activity?.channel,
      activity?.actor_class,
      activity?.intent_class,
      activity?.request_summary,
      activity?.outcome,
      activity?.resolved_person_id,
      activity?.resolved_area_id,
    ]
      .map((item) => String(item || "").toLowerCase())
      .join(" ");

    return blob.includes(term);
  }

  _filteredActivityTimeline() {
    const activeFilter = String(this._activityTimelineFilter || "all").toLowerCase();
    const searchTerm = this._activityTimelineSearch || "";
    const rows = Array.isArray(this._activityTimeline) ? this._activityTimeline : [];

    return rows.filter((activity) => (
      this._activityMatchesFilter(activity, activeFilter)
      && this._activityMatchesSearch(activity, searchTerm)
    ));
  }

  _renderBreadcrumb(items) {
    return `
      <div class="cg-breadcrumb">
        ${items.map((item, index) => {
          const isLast = index === items.length - 1;
          const label = this._escapeHtml(item.label || "");

          if (!isLast) {
            if (item.nav === "home") {
              return `<button data-nav="home">${label}</button> &gt; `;
            }
            if (item.roomId) {
              return `<button data-nav-room="${this._escapeHtml(item.roomId)}">${label}</button> &gt; `;
            }
            return `<span>${label}</span> &gt; `;
          }

          return `<span class="cg-breadcrumb-current">${label}</span>`;
        }).join("")}
      </div>
    `;
  }

  _availableRoomCards(catalog) {
    const cards = [];
    const roomCatalog = catalog || {};

    const pushIfAvailable = (fieldKey, title, options) => {
      const rows = Array.isArray(options) ? options : [];
      if (rows.length) {
        cards.push({ fieldKey, title, options: rows });
      }
    };

    pushIfAvailable("light_entity_ids", "Lights", roomCatalog.light_entity_ids);
    pushIfAvailable("lamp_entity_ids", "Lamps", roomCatalog.lamp_entity_ids);
    pushIfAvailable("speaker_entity_ids", "Speakers", roomCatalog.speaker_entity_ids);
    pushIfAvailable("voice_device_entity_ids", "Voice Assistants", roomCatalog.voice_device_entity_ids);
    pushIfAvailable("shade_entity_ids", "Shades", roomCatalog.shade_entity_ids);
    pushIfAvailable("room_sensor_entity_ids", "Room Sensors", roomCatalog.room_sensor_entity_ids);

    if (this._assetIntelligenceConnected) {
      pushIfAvailable("room_health_entity_ids", "Room Environment (Asset Intelligence)", roomCatalog.room_health_entity_ids);
      pushIfAvailable("human_health_entity_ids", "Human Health (Asset Intelligence)", roomCatalog.human_health_entity_ids);
    }

    pushIfAvailable("tv_entity_ids", "TV", roomCatalog.tv_entity_ids);
    pushIfAvailable("dashboard_entity_ids", "Dashboards", roomCatalog.dashboard_entity_ids);
    pushIfAvailable("media_player_entity_ids", "Media Players", roomCatalog.media_player_entity_ids);
    pushIfAvailable("other_entity_ids", "Other Room Elements", roomCatalog.other_entity_ids);
    return cards;
  }

  _renderEditMergeDialog() {
    const compositeId = this._editMergeCompositeId;
    if (!compositeId) return "";

    const composite = this._composites[compositeId];
    if (!composite) return "";

    const memberAreaIds = Array.from(new Set(Array.isArray(this._editMergeAreaIds) ? this._editMergeAreaIds : []));
    const memberRoomMarkup = memberAreaIds.length
      ? memberAreaIds.map((areaId) => {
          const area = this._areas.find((item) => item.id === areaId);
          const label = area?.name || areaId;
          return `
            <label class="cg-edit-merge-item">
              <input class="cg-edit-merge-room" type="checkbox" value="${this._escapeHtml(areaId)}" checked>
              <span>${this._escapeHtml(label)}</span>
            </label>
          `;
        }).join("")
      : `<div class="cg-muted">No rooms are currently assigned to this composite.</div>`;

    return `
      <ha-dialog
        open
        scrimClickAction
        escapeKeyAction
        hideActions
        data-edit-merge-dialog
        header-title="Edit Merge"
      >
        <div style="padding: 0 16px 16px; display: grid; gap: 12px;">
          <div class="cg-modal-copy">Update the composite name and member rooms.</div>
          <label class="cg-modal-field">
            <span>Composite Name</span>
            <input id="cg-edit-merge-name" type="text" value="${this._escapeHtml(this._editMergeName || composite.name || compositeId)}">
          </label>
          <div class="cg-modal-field">
            <span>Rooms in Composite</span>
            <div class="cg-edit-merge-list">
              ${memberRoomMarkup}
            </div>
          </div>
          <div class="cg-modal-hint">Uncheck a room to remove it from the composite.</div>
          <div class="cg-modal-error">${this._escapeHtml(this._editMergeError || "")}</div>
        </div>
        <ha-dialog-footer slot="footer">
          <ha-button slot="secondaryAction" appearance="plain" data-edit-merge-cancel>Cancel</ha-button>
          <ha-button slot="primaryAction" variant="brand" data-edit-merge-update>Update</ha-button>
        </ha-dialog-footer>
      </ha-dialog>
    `;
  }

  _configuredCardCount(room, cards) {
    if (!room || !cards.length) return 0;
    return cards.reduce((count, card) => {
      const selected = this._selectedIds(room, card.fieldKey);
      return count + (selected.length ? 1 : 0);
    }, 0);
  }

  _memberAreaNames(areaIds) {
    const ids = Array.isArray(areaIds) ? areaIds : [];
    return ids
      .map((areaId) => this._areas.find((item) => item.id === areaId)?.name || areaId)
      .filter(Boolean);
  }

  _areaName(areaId) {
    if (!areaId) return "room";
    return this._areas.find((item) => item.id === areaId)?.name || areaId;
  }

  _isSameFloorAreaSet(areaIds) {
    const ids = Array.isArray(areaIds) ? areaIds : [];
    if (ids.length <= 1) return true;
    const floorIds = new Set(
      ids
        .map((id) => this._areas.find((item) => item.id === id)?.floor_id || null)
    );
    return floorIds.size <= 1;
  }

  async _saveCompositeConfig(compositeId) {
    const composite = this._composites[compositeId] || {};
    const nameInput = this.querySelector(`#cg-composite-name-${CSS.escape(compositeId)}`);
    const selectedAreaIds = this._collectSelected(this.querySelector(`#cg-composite-areas-${CSS.escape(compositeId)}`));
    const status = this.querySelector(`.cg-composite-status[data-composite-id="${CSS.escape(compositeId)}"]`);
    const mergedAssetGroups = this._combinedAssetGroupsForAreaIds(selectedAreaIds);
    const combinedField = (fieldKey) => this._combinedFieldEntityIdsForAreaIds(selectedAreaIds, fieldKey);

    if (!this._isSameFloorAreaSet(selectedAreaIds)) {
      if (status) status.textContent = "Save failed: selected rooms must be on the same floor";
      return;
    }

    if (status) status.textContent = "Saving composite...";
    try {
      const payload = {
        composite_id: compositeId,
        name: nameInput?.value?.trim() || composite.name || compositeId,
        area_ids: selectedAreaIds,
        asset_groups: mergedAssetGroups,
        room_sensor_entity_ids: combinedField("room_sensor_entity_ids"),
        room_health_entity_ids: combinedField("room_health_entity_ids"),
        human_health_entity_ids: combinedField("human_health_entity_ids"),
        light_entity_ids: combinedField("light_entity_ids"),
        shade_entity_ids: combinedField("shade_entity_ids"),
        speaker_entity_ids: combinedField("speaker_entity_ids"),
        voice_device_entity_ids: combinedField("voice_device_entity_ids"),
        dashboard_entity_ids: combinedField("dashboard_entity_ids"),
        media_player_entity_ids: combinedField("media_player_entity_ids"),
        other_entity_ids: combinedField("other_entity_ids"),
      };
      await this._hass.callService(
        "concierge",
        "update_composite_config",
        payload,
        undefined,
        true,
        true
      );
      this._clearActiveFormDraft();
      await this._load();
      if (!this._composites[compositeId]) {
        this._goHome();
        return;
      }
      if (status) status.textContent = "Saved";
    } catch (err) {
      if (status) status.textContent = `Save failed: ${err?.message || err}`;
    }
  }

  async _createCompositeFromSelection() {
    this._syncMergeSelectionFromDom();
    const nameInput = this.querySelector("#cg-merge-name");
    const status = this.querySelector(".cg-merge-status");
    const selectedAreaIds = Array.from(new Set((this._mergeDraftAreaIds || []).filter(Boolean)));
    this._mergeLog("submit composite", {
      selectedAreaIds,
      count: selectedAreaIds.length,
      mergeDraftName: this._mergeDraftName,
    });

    if (selectedAreaIds.length < 2) {
      if (status) status.textContent = "Select at least two rooms to merge.";
      return;
    }

    if (!this._isSameFloorAreaSet(selectedAreaIds)) {
      if (status) status.textContent = "Selected rooms must be on the same floor.";
      return;
    }

    const name = (nameInput?.value || this._mergeDraftName || "").trim();
    if (!name) {
      if (status) status.textContent = "Enter a merged room name.";
      return;
    }

    const baseId = this._slugify(name);
    let compositeId = baseId;
    let counter = 2;
    while (this._composites[compositeId]) {
      compositeId = `${baseId}_${counter}`;
      counter += 1;
    }

    if (status) status.textContent = "Creating merged room...";
    try {
      await this._hass.callService(
        "concierge",
        "update_composite_config",
        {
          composite_id: compositeId,
          name,
          area_ids: selectedAreaIds,
        },
        undefined,
        true,
        true
      );
      this._mergeMode = false;
      this._mergeDraftName = "";
      this._mergeDraftAreaIds = [];
      await this._load();
      if (status) status.textContent = "Merged room created.";
    } catch (err) {
      if (status) status.textContent = `Create failed: ${err?.message || err}`;
    }
  }

  async _saveGlobalSettings(options = {}) {
    const closeOnSuccess = Boolean(options?.closeOnSuccess);
    const weatherSourceEntityIds = this._collectGlobalSourceEntityIds("weather");
    const newsSourceEntityIds = this._collectGlobalSourceEntityIds("news");
    const alarmEntityId = this.querySelector("#cg-alarm-entity")?.value || "";

    const status = this.querySelector(".cg-global-settings-dialog .cg-global-status") || this.querySelector(".cg-global-status");
    if (status) status.textContent = "Saving global settings...";

    try {
      await this._hass.callService("concierge", "update_global_context", {
        context_type: "weather",
        enabled: weatherSourceEntityIds.length > 0,
        options: { source_entity_ids: weatherSourceEntityIds },
      }, undefined, true, true);
      await this._hass.callService("concierge", "update_global_context", {
        context_type: "news",
        enabled: newsSourceEntityIds.length > 0,
        options: { source_entity_ids: newsSourceEntityIds },
      }, undefined, true, true);
      await this._hass.callService("concierge", "update_global_context", {
        context_type: "alarm_status",
        enabled: Boolean(alarmEntityId),
        options: alarmEntityId ? { entity_id: alarmEntityId } : {},
      }, undefined, true, true);

      // Keep local global state in sync so the selected rows remain visible after save.
      this._globalFeatures = {
        ...this._globalFeatures,
        weather: {
          enabled: weatherSourceEntityIds.length > 0,
          options: { source_entity_ids: weatherSourceEntityIds },
        },
        news: {
          enabled: newsSourceEntityIds.length > 0,
          options: { source_entity_ids: newsSourceEntityIds },
        },
        alarm_status: {
          enabled: Boolean(alarmEntityId),
          options: alarmEntityId ? { entity_id: alarmEntityId } : {},
        },
      };
      this._globalContextUsage = {
        ...this._globalContextUsage,
        weather: {
          enabled: weatherSourceEntityIds.length > 0,
          options: { source_entity_ids: weatherSourceEntityIds },
        },
        news: {
          enabled: newsSourceEntityIds.length > 0,
          options: { source_entity_ids: newsSourceEntityIds },
        },
        alarm_status: {
          enabled: Boolean(alarmEntityId),
          options: alarmEntityId ? { entity_id: alarmEntityId } : {},
        },
      };

      this._clearActiveFormDraft();
      if (status) status.textContent = "Saved";
      if (closeOnSuccess) {
        this._globalSettingsDialogOpen = false;
        this._render();
      }
    } catch (err) {
      if (status) status.textContent = `Save failed: ${err?.message || err}`;
    }
  }

  async _exportActivityArchive() {
    const status = this.querySelector(".cg-archive-status");
    const capExtendedHistory = Boolean(this._integrationOptions?.capabilities?.cap_extended_history);
    if (!capExtendedHistory) {
      if (status) status.textContent = "Archive export is unavailable until attached storage and archive export are enabled in integration options.";
      return;
    }
    if (!this._archiveStatus?.destination_configured) {
      if (status) status.textContent = "Configure archive destination in integration options before export.";
      return;
    }

    if (status) status.textContent = "Exporting archive...";
    try {
      const result = await this._hass.callService(
        "concierge",
        "export_activity_archive",
        {},
        undefined,
        true,
        true
      );
      const itemCount = result?.item_count;
      const archiveUri = result?.archive_uri;
      if (status) {
        status.textContent = archiveUri
          ? `Exported ${itemCount ?? 0} activities to ${archiveUri}`
          : "Archive export completed.";
      }
    } catch (err) {
      if (status) status.textContent = `Export failed: ${err?.message || err}`;
    }
  }

  async _loadActivityTimeline(renderOnComplete = true, areaId = "") {
    if (this._activityTimelineLoading) return;
    this._activityTimelineLoading = true;
    try {
      const payload = areaId ? { area_id: areaId } : {};
      const result = await this._hass.callService(
        "concierge",
        "get_activity_timeline",
        payload,
        undefined,
        true,
        true
      );
      const activities = Array.isArray(result?.activities) ? result.activities : [];
      activities.sort((left, right) => String(right?.started_at || "").localeCompare(String(left?.started_at || "")));
      this._activityTimeline = activities.slice(0, 25);
      this._activityTimelineLoaded = true;
    } catch (err) {
      // no-op: keep existing timeline view without failing panel render.
    } finally {
      this._activityTimelineLoading = false;
      if (renderOnComplete) this._render();
    }
  }

  async _loadTtsCatalog(force = false) {
    if (this._ttsCatalogLoading) return;
    if (!force && this._ttsCatalogLoaded && (Date.now() - this._ttsCatalogLoadedAt) < 15000) {
      return;
    }

    this._ttsCatalogLoading = true;
    try {
      const response = await this._authFetch("/api/concierge/tts_catalog", 12000);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      this._ttsCatalog = this._normalizeTtsCatalog(await response.json());
      this._ttsCatalogProvider = this._ttsCatalog.provider || "none";
      this._ttsCatalogLoaded = true;
      this._ttsCatalogLoadedAt = Date.now();
    } catch (err) {
      this._ttsCatalog = { provider: "none", defaultLanguage: "", languages: [], voicesByLanguage: {} };
      this._ttsCatalogProvider = "none";
      this._ttsCatalogLoaded = true;
      this._ttsCatalogLoadedAt = Date.now();
    } finally {
      this._ttsCatalogLoading = false;
      if (this._selectedAreaId && !this._selectedCompositeId && !this._selectedPersonId) {
        this._render();
      }
    }
  }

  _openRoomVoiceDialog(areaId) {
    this._roomVoiceDialog = {
      open: true,
      areaId,
      message: "Hello. How can I assist?",
      playing: false,
      error: "",
    };

    const existingDialog = document.querySelector("ha-dialog[data-room-voice-preview-dialog]");
    if (existingDialog) {
      existingDialog.remove();
    }

    const dialog = document.createElement("ha-dialog");
    dialog.setAttribute("data-room-voice-preview-dialog", "true");
    dialog.setAttribute("header-title", "Try text-to-speech");
    dialog.setAttribute("type", "dialog");
    dialog.open = true;
    dialog.scrimClickAction = true;
    dialog.escapeKeyAction = true;

    dialog.innerHTML = `
      <div class="cg-room-voice-dialog-body" style="padding: 0 0 8px;">
        <div class="cg-room-voice-input-shell" style="background: var(--secondary-background-color); border-radius: 6px; padding: 16px 20px 18px; border-bottom: 1px solid var(--divider-color);">
          <label for="cg-room-voice-message" style="display:block; font-size: 13px; color: var(--secondary-text-color); margin-bottom: 6px;">Message</label>
          <textarea id="cg-room-voice-message" rows="5" style="width:100%; min-height: 116px; resize: vertical; border: 0; outline: none; background: transparent; color: var(--primary-text-color); font: inherit; padding: 0; box-sizing: border-box;">${this._escapeHtml(this._roomVoiceDialog?.message || "Hello. How can I assist?")}</textarea>
        </div>
        <div data-room-voice-error style="display:none; color: var(--error-color); padding: 10px 20px 0;"></div>
      </div>
      <ha-dialog-footer slot="footer">
        <ha-button slot="primaryAction" variant="brand" data-room-voice-play data-area-id="${this._escapeHtml(areaId)}">Play</ha-button>
      </ha-dialog-footer>
    `;

    document.body.appendChild(dialog);

    const messageField = dialog.querySelector("#cg-room-voice-message");
    if (messageField) {
      messageField.value = this._roomVoiceDialog?.message || "Hello. How can I assist?";
      messageField.focus();
      messageField.setSelectionRange(messageField.value.length, messageField.value.length);
    }

    const playBtn = dialog.querySelector("[data-room-voice-play]");
    const errorRow = dialog.querySelector("[data-room-voice-error]");

    const syncDialogState = () => {
      const currentMessage = String(messageField?.value || "").trim();
      this._roomVoiceDialog.message = currentMessage || "";
      if (playBtn) {
        playBtn.disabled = !currentMessage || Boolean(this._roomVoiceDialog.playing);
        playBtn.textContent = this._roomVoiceDialog.playing ? "Playing..." : "Play";
      }
      if (errorRow) {
        const hasError = Boolean(this._roomVoiceDialog.error);
        errorRow.style.display = hasError ? "block" : "none";
        errorRow.textContent = hasError ? this._roomVoiceDialog.error : "";
      }
    };

    messageField?.addEventListener("input", () => {
      this._roomVoiceDialog.error = "";
      syncDialogState();
    });

    playBtn?.addEventListener("click", () => {
      const dialogAreaId = playBtn.getAttribute("data-area-id");
      if (dialogAreaId) this._listenRoomPersona(dialogAreaId);
    });

    dialog.addEventListener("closed", () => this._closeRoomVoiceDialog());
    syncDialogState();
  }

  _closeRoomVoiceDialog() {
    this._stopRoomVoicePreviewAudio();
    const existingDialog = document.querySelector("ha-dialog[data-room-voice-preview-dialog]");
    if (existingDialog) {
      existingDialog.remove();
    }
    this._roomVoiceDialog = {
      open: false,
      areaId: "",
      message: "Hello. How can I assist?",
      playing: false,
      error: "",
    };
  }

  _stopRoomVoicePreviewAudio() {
    const activeAudio = this._roomVoicePreviewAudio;
    this._roomVoicePreviewAudio = null;
    if (!activeAudio) return;
    try {
      activeAudio.pause();
    } catch (err) {
      // no-op
    }
    try {
      activeAudio.removeAttribute("src");
      activeAudio.load();
    } catch (err) {
      // no-op
    }
  }

  _describeError(err) {
    const direct = String(
      err?.body?.message
      || err?.body?.error
      || err?.error?.message
      || err?.error
      || err?.message
      || ""
    ).trim();
    if (direct) return direct;
    if (typeof err === "string") return err;
    try {
      return JSON.stringify(err);
    } catch (jsonErr) {
      return String(err || "Unknown error");
    }
  }

  async _requestBrowserTtsUrl(provider, message, language, voice, instructions) {
    const engineId = CONCIERGE_TTS_ENGINE_IDS[provider] || provider;
    const isOpenAiTts = engineId === "tts.openai_tts" || provider === "openai_conversation";
    const options = {};
    const payload = {
      engine_id: engineId,
      message,
      cache: false,
    };

    if (language) payload.language = language;
    if (voice) options.voice = voice;
    if (instructions && isOpenAiTts) options.instructions = instructions;
    if (Object.keys(options).length) payload.options = options;

    const attempts = [];
    const addAttempt = (nextPayload) => {
      const key = JSON.stringify(nextPayload);
      if (!attempts.find((item) => item.key === key)) {
        attempts.push({ key, payload: nextPayload });
      }
    };

    addAttempt(payload);

    if (payload.options?.instructions) {
      const withoutInstructions = {
        ...payload,
        options: { ...payload.options },
      };
      delete withoutInstructions.options.instructions;
      if (!Object.keys(withoutInstructions.options).length) {
        delete withoutInstructions.options;
      }
      addAttempt(withoutInstructions);
    }

    if (payload.language) {
      const withoutLanguage = { ...payload };
      delete withoutLanguage.language;
      addAttempt(withoutLanguage);

      if (payload.options?.instructions) {
        const withoutLanguageAndInstructions = {
          ...withoutLanguage,
          options: { ...(withoutLanguage.options || {}) },
        };
        delete withoutLanguageAndInstructions.options.instructions;
        if (!Object.keys(withoutLanguageAndInstructions.options).length) {
          delete withoutLanguageAndInstructions.options;
        }
        addAttempt(withoutLanguageAndInstructions);
      }
    }

    let lastError = null;
    for (const attempt of attempts) {
      try {
        return await this._hass.callApi("POST", "tts_get_url", attempt.payload);
      } catch (err) {
        lastError = err;
      }
    }

    throw new Error(this._describeError(lastError));
  }

  async _playBrowserTtsPreview(provider, message, language, voice, instructions) {
    this._stopRoomVoicePreviewAudio();

    const audio = new Audio();
    this._roomVoicePreviewAudio = audio;

    try {
      audio.play();
    } catch (err) {
      // Browsers may reject the prewarm play before src is assigned.
    }

    const result = await this._requestBrowserTtsUrl(provider, message, language, voice, instructions);
    const audioUrl = String(result?.path || result?.url || "").trim();
    if (!audioUrl) {
      this._stopRoomVoicePreviewAudio();
      throw new Error("Home Assistant did not return an audio preview URL.");
    }

    await new Promise((resolve, reject) => {
      let settled = false;
      const timeoutId = window.setTimeout(() => {
        finishReject(new Error("Timed out waiting for audio preview to start."));
      }, 10000);

      const cleanup = () => {
        window.clearTimeout(timeoutId);
        audio.removeEventListener("canplaythrough", handleCanPlayThrough);
        audio.removeEventListener("playing", handlePlaying);
        audio.removeEventListener("error", handleError);
      };

      const finishResolve = () => {
        if (settled) return;
        settled = true;
        cleanup();
        resolve();
      };

      const finishReject = (error) => {
        if (settled) return;
        settled = true;
        cleanup();
        if (this._roomVoicePreviewAudio === audio) {
          this._roomVoicePreviewAudio = null;
          try {
            audio.pause();
          } catch (err) {
            // no-op
          }
        }
        reject(error instanceof Error ? error : new Error(String(error || "Unable to play audio preview.")));
      };

      const tryPlay = () => {
        if (this._roomVoicePreviewAudio !== audio) {
          finishReject(new Error("Audio preview was replaced before playback started."));
          return;
        }
        audio.play().catch((err) => finishReject(err));
      };

      const handleCanPlayThrough = () => {
        tryPlay();
      };

      const handlePlaying = () => {
        finishResolve();
      };

      const handleError = () => {
        finishReject(new Error("Unable to play the generated audio preview in this browser."));
      };

      audio.addEventListener("canplaythrough", handleCanPlayThrough);
      audio.addEventListener("playing", handlePlaying);
      audio.addEventListener("error", handleError);
      audio.src = audioUrl;
    });
  }

  _openActivityDetails(areaId, activityId) {
    if (!areaId || !activityId) return;
    this._activityDetailsDialog = {
      open: true,
      areaId,
      activityId,
    };
    this._render();
  }

  _closeActivityDetails() {
    this._activityDetailsDialog = {
      open: false,
      areaId: "",
      activityId: "",
    };
    this._render();
  }

  _activityCategory(activity) {
    const intentClass = String(activity?.intent_class || "").toLowerCase();
    if (intentClass !== "room_config_update") {
      return intentClass || "unknown";
    }

    const diffRef = Array.isArray(activity?.external_refs)
      ? activity.external_refs.find((ref) => String(ref?.ref_type || "") === "room_config_diff")
      : null;
    const fields = new Set(
      (Array.isArray(diffRef?.changes) ? diffRef.changes : [])
        .map((change) => String(change?.field || ""))
        .filter(Boolean)
    );

    const roomDeviceFields = new Set([
      "device_groups",
      "voice_device_entity_ids",
      "media_player_entity_ids",
      "speaker_entity_ids",
      "light_entity_ids",
      "lamp_entity_ids",
      "shade_entity_ids",
      "tv_entity_ids",
      "room_sensor_entity_ids",
    ]);
    const informationFields = new Set([
      "weather_source_entity_ids",
      "news_source_entity_ids",
      "asset_groups",
      "environment_information_outputs",
      "ai_knowledge_enabled",
      "human_health_entity_ids",
      "room_health_entity_ids",
      "dashboard_entity_ids",
      "other_entity_ids",
    ]);
    const personaFields = new Set(["persona", "persona_prompt", "tts_voice", "tts_language", "posture"]);

    const hasDevice = Array.from(fields).some((field) => roomDeviceFields.has(field));
    const hasInfo = Array.from(fields).some((field) => informationFields.has(field));
    const hasPersona = Array.from(fields).some((field) => personaFields.has(field));

    if ((hasDevice && hasInfo) || (hasDevice && hasPersona) || (hasInfo && hasPersona)) {
      return "Room Configuration";
    }
    if (hasDevice) return "Room Devices";
    if (hasInfo) return "Information Sources";
    if (hasPersona) return "Room Persona";
    return "Room Configuration";
  }

  _openLatestRoomSaveDialog(areaId) {
    if (!areaId) return;
    const rows = Array.isArray(this._activityTimeline) ? this._activityTimeline : [];
    const latest = rows.find((event) => (
      String(event?.resolved_area_id || "") === String(areaId)
      && String(event?.intent_class || "").toLowerCase() === "room_config_update"
    ));
    const activityId = String(latest?.activity_id || "");
    if (!activityId) return;

    this._activityDetailsDialog = {
      open: true,
      areaId,
      activityId,
    };
    this._render();
  }

  _openGlobalSettingsDialog() {
    this._globalSettingsDialogOpen = true;
    this._render();
  }

  _closeGlobalSettingsDialog() {
    this._globalSettingsDialogOpen = false;
    this._render();
  }

  _renderGlobalSettingsDialog(weatherSourceEntityIds, newsSourceEntityIds, alarmEntityId) {
    if (!this._globalSettingsDialogOpen) return "";

    const archiveStatus = this._archiveStatus || {};
    const archiveDestinationConfigured = Boolean(archiveStatus.destination_configured);
    const archiveDestinationUri = String(archiveStatus.destination_uri || "");
    const archiveEnabled = Boolean(archiveStatus.archive_enabled);
    const archiveIncludeRefs = Boolean(archiveStatus.include_reference_excerpts);
    const haPurgeKeepDays = Math.max(1, Number(archiveStatus.ha_purge_keep_days || 10));
    const archiveCaptureAgeDays = Math.max(1, Number(archiveStatus.archive_capture_age_days || Math.max(1, haPurgeKeepDays - 2)));
    const archiveRetentionDays = Math.max(1, Number(archiveStatus.archive_retention_days || 30));
    const integrationOptions = this._integrationOptions || {};
    const capabilityFlags = integrationOptions.capabilities || {};

    return `
      <ha-dialog
        open
        scrimClickAction
        escapeKeyAction
        hideActions
        data-global-settings-dialog
        header-title="Global Settings"
        class="cg-global-settings-dialog"
      >
        <div style="padding: 0 16px 16px; display: grid; gap: 14px;">
          <div class="cg-global-copy">Global weather/news/alarm sources are configured here. Integration-level options remain in the integration gear.</div>
          <div class="cg-global-grid">
            ${this._renderGlobalSourceEditor("weather", "Outside Weather", this._globalCatalog.weather_entity_ids, weatherSourceEntityIds, "No weather integrations found")}
            ${this._renderGlobalSourceEditor("news", "News", this._globalCatalog.news_entity_ids, newsSourceEntityIds, "No news integrations found")}
            <div class="cg-global-item">
              <label for="cg-alarm-entity">Alarm Status</label>
              ${this._renderCategorySelect("cg-alarm-entity", this._globalCatalog.alarm_entity_ids, alarmEntityId, "No alarm integrations found")}
            </div>
          </div>

          <div class="cg-config-card" style="box-shadow:none; border:1px solid var(--divider-color);">
            <div class="cg-config-title" style="font-size:14px;">Integration Settings Snapshot</div>
            <div class="cg-room-meta">AI enabled: ${this._escapeHtml(integrationOptions.ai_enabled ? "Yes" : "No")}</div>
            <div class="cg-room-meta">Action provider: ${this._escapeHtml(integrationOptions.action_provider || "none")}</div>
            <div class="cg-room-meta">AI local-first: ${this._escapeHtml(integrationOptions.ai_local_first ? "Yes" : "No")}</div>
            <div class="cg-room-meta">TTS enabled: ${this._escapeHtml(integrationOptions.tts_enabled ? "Yes" : "No")}</div>
            <div class="cg-room-meta">TTS provider: ${this._escapeHtml(integrationOptions.tts_provider || "none")}</div>
            <div class="cg-room-meta">Media provider: ${this._escapeHtml(integrationOptions.media_provider || "none")}</div>
            <div class="cg-room-meta">Asset Intelligence link: ${this._escapeHtml(integrationOptions.asset_intelligence_provider || "none")}</div>
            <div class="cg-room-meta">Capability (AI): ${this._escapeHtml(capabilityFlags.cap_ai ? "Enabled" : "Disabled")}</div>
            <div class="cg-room-meta">Capability (Persona): ${this._escapeHtml(capabilityFlags.cap_persona ? "Enabled" : "Disabled")}</div>
            <div class="cg-room-meta">Capability (Assets): ${this._escapeHtml(capabilityFlags.cap_assets ? "Enabled" : "Disabled")}</div>
            <div class="cg-room-meta">Capability (Voice Enrollment): ${this._escapeHtml(capabilityFlags.cap_voice_enrollment ? "Enabled" : "Disabled")}</div>
            <div class="cg-room-meta">Audit archive enabled: ${this._escapeHtml(archiveEnabled ? "Yes" : "No")}</div>
            <div class="cg-room-meta">Destination: ${this._escapeHtml(archiveDestinationUri || "Not configured")}</div>
            <div class="cg-room-meta">Archive retention days: ${this._escapeHtml(String(archiveRetentionDays))}</div>
            <div class="cg-room-meta">HA purge keep days: ${this._escapeHtml(String(haPurgeKeepDays))}</div>
            <div class="cg-room-meta">Archive capture threshold: ${this._escapeHtml(String(archiveCaptureAgeDays))} days old</div>
            <div class="cg-room-meta">Include reference excerpts: ${this._escapeHtml(archiveIncludeRefs ? "Yes" : "No")}</div>
            <div class="cg-muted" style="margin-top:8px;">${archiveDestinationConfigured ? "To change archive wiring, open the integration options gear." : "Archive destination is not configured in integration options gear."}</div>
          </div>

          <div class="cg-global-status"></div>
        </div>
        <ha-dialog-footer slot="footer">
          <ha-button slot="secondaryAction" appearance="plain" data-close-global-settings>Cancel</ha-button>
          <ha-button slot="primaryAction" variant="brand" data-save-global-settings>Save</ha-button>
        </ha-dialog-footer>
      </ha-dialog>
    `;
  }

  async _listenRoomPersona(areaId) {
    const status = this.querySelector(`.cg-room-status[data-area-id="${CSS.escape(areaId)}"]`);
    const provider = String(this._integrationOptions?.tts_provider || "none");
    const ttsEnabled = Boolean(this._integrationOptions?.tts_enabled);
    if (!ttsEnabled || provider === "none") {
      if (status) status.textContent = "Enable TTS provider in Concierge options before Listen.";
      return;
    }

    const getHaSelectValue = (fieldKey) => {
      const el = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="${CSS.escape(fieldKey)}"]`);
      if (!el) return "";
      const selectedItem = el.querySelector("ha-list-item[selected], mwc-list-item[selected]");
      if (selectedItem) {
        return String(selectedItem.value || selectedItem.getAttribute("value") || "").trim();
      }
      return String(el.value || "").trim();
    };

    const voiceSelection = getHaSelectValue("tts_voice");
    const languageSelection = getHaSelectValue("tts_language");
    const personaPrompt = String(this.querySelector(`textarea[data-area-id="${CSS.escape(areaId)}"][data-field-key="persona_prompt"]`)?.value || "").trim();
    const messageField = this.querySelector("#cg-room-voice-message");
    const message = String(messageField?.value || "Hello. How can I assist?").trim() || "Hello. How can I assist?";
    this._roomVoiceDialog.message = message;
    this._roomVoiceDialog.playing = true;
    this._roomVoiceDialog.error = "";
    const activeDialog = document.querySelector("ha-dialog[data-room-voice-preview-dialog]");
    const activePlayButton = activeDialog?.querySelector("[data-room-voice-play]");
    const activeErrorRow = activeDialog?.querySelector("[data-room-voice-error]");
    if (activePlayButton) {
      activePlayButton.disabled = true;
      activePlayButton.textContent = "Playing...";
    }
    if (activeErrorRow) {
      activeErrorRow.style.display = "none";
      activeErrorRow.textContent = "";
    }

    if (status) status.textContent = "Playing browser voice preview...";
    try {
      await this._playBrowserTtsPreview(
        provider,
        message,
        languageSelection || undefined,
        voiceSelection || undefined,
        personaPrompt || undefined,
      );
      if (status) status.textContent = "Browser voice preview started.";
      this._roomVoiceDialog.playing = false;
      if (activePlayButton) {
        activePlayButton.disabled = false;
        activePlayButton.textContent = "Play";
      }
    } catch (err) {
      const errorText = this._describeError(err);
      this._roomVoiceDialog.playing = false;
      this._roomVoiceDialog.error = `Unable to play audio. ${errorText}`;
      if (activePlayButton) {
        activePlayButton.disabled = false;
        activePlayButton.textContent = "Play";
      }
      if (activeErrorRow) {
        activeErrorRow.style.display = "block";
        activeErrorRow.textContent = this._roomVoiceDialog.error;
      }
      if (status) status.textContent = `Listen failed: ${errorText}`;
    }
  }

  _capabilityFlags() {
    return {
      cap_ai: Boolean(this._integrationOptions?.capabilities?.cap_ai),
      cap_tts: Boolean(this._integrationOptions?.capabilities?.cap_tts),
      cap_persona: Boolean(this._integrationOptions?.capabilities?.cap_persona),
      cap_assets: Boolean(this._integrationOptions?.capabilities?.cap_assets),
      cap_voice_enrollment: Boolean(this._integrationOptions?.capabilities?.cap_voice_enrollment),
      cap_extended_history: Boolean(this._integrationOptions?.capabilities?.cap_extended_history),
    };
  }

  _normalizePersonaPayload(payload) {
    const flags = this._capabilityFlags();
    const normalized = { ...(payload || {}) };

    if (!flags.cap_persona) {
      normalized.persona = "";
      normalized.persona_prompt = "";
      normalized.tts_voice = "";
      normalized.tts_language = "";
      return normalized;
    }

    if (!flags.cap_tts) {
      normalized.tts_voice = "";
      normalized.tts_language = "";
    }

    return normalized;
  }

  _normalizeInformationSourcesPayload(payload) {
    const flags = this._capabilityFlags();
    const normalized = { ...(payload || {}) };

    if (!flags.cap_ai) {
      normalized.ai_knowledge_enabled = false;
    }

    if (!flags.cap_assets) {
      normalized.asset_groups = [];
      normalized.environment_information_outputs = [];
    }

    return normalized;
  }

  _normalizePersonProfilePayload(payload) {
    const flags = this._capabilityFlags();
    const normalized = { ...(payload || {}) };

    if (!flags.cap_ai) {
      normalized.minor_allow_general_qna = false;
      normalized.minor_allowed_intent_classes = ["room_context_info", "household_help"];
      normalized.minor_content_filter_level = "strict";
    }

    if (!flags.cap_tts) {
      delete normalized.voice_profile_id;
    }

    if (normalized?.consent && typeof normalized.consent === "object") {
      const interactionTargets = normalized.consent.interaction_targets && typeof normalized.consent.interaction_targets === "object"
        ? { ...normalized.consent.interaction_targets }
        : {};
      if (!flags.cap_tts) {
        interactionTargets.mobile_voice_endpoint_enabled = false;
      }
      normalized.consent = {
        ...normalized.consent,
        interaction_targets: interactionTargets,
      };
    }

    return normalized;
  }

  async _saveRoomPersona(areaId) {
    const postureSelect = this.querySelector(`select[data-area-id="${CSS.escape(areaId)}"][data-field-key="posture"]`);
    const currentRoom = this._rooms?.[areaId] || {};
    const readRoomField = (fieldKey) => {
      const el = this.querySelector(`[data-area-id="${CSS.escape(areaId)}"][data-field-key="${CSS.escape(fieldKey)}"]`);
      if (!el) return "";
      const selectedItem = el.querySelector("ha-list-item[selected], mwc-list-item[selected]");
      if (selectedItem) {
        return String(selectedItem.value || selectedItem.getAttribute("value") || "").trim();
      }
      return String(el.value || "").trim();
    };
    const selectedVoiceValue = readRoomField("tts_voice");

    const payload = this._normalizePersonaPayload({
      area_id: areaId,
      posture: postureSelect ? postureSelect.value : (currentRoom.posture || "day"),
      tts_voice: selectedVoiceValue,
      tts_language: readRoomField("tts_language"),
      persona: this.querySelector(`input[data-area-id="${CSS.escape(areaId)}"][data-field-key="persona"]`)?.value || currentRoom.persona || "",
      persona_prompt: this.querySelector(`textarea[data-area-id="${CSS.escape(areaId)}"][data-field-key="persona_prompt"]`)?.value || "",
    });

    const status = this.querySelector(`.cg-room-status[data-area-id="${CSS.escape(areaId)}"]`);
    if (status) status.textContent = "Saving room...";
    try {
      await this._hass.callService("concierge", "update_room_config", payload, undefined, true, true);
      this._clearActiveFormDraft();
      this._clearRoomPersonaDraft(areaId);
      this._rooms[areaId] = { ...(this._rooms[areaId] || {}), ...payload };
      if (this._selectedAreaId === areaId) {
        await this._loadActivityTimeline(false, areaId);
        this._openLatestRoomSaveDialog(areaId);
      }
      if (status) status.textContent = "Saved";
    } catch (err) {
      if (status) status.textContent = `Save failed: ${err?.message || err}`;
    }
  }

  async _saveCompositePersona(compositeId) {
    if (!compositeId) return;
    const currentComposite = this._composites?.[compositeId] || {};
    const readCompositeField = (fieldKey) => {
      const el = this.querySelector(`[data-area-id="${CSS.escape(compositeId)}"][data-field-key="${CSS.escape(fieldKey)}"]`);
      if (!el) return "";
      const selectedItem = el.querySelector("ha-list-item[selected], mwc-list-item[selected]");
      if (selectedItem) {
        return String(selectedItem.value || selectedItem.getAttribute("value") || "").trim();
      }
      return String(el.value || "").trim();
    };

    const payload = this._normalizePersonaPayload({
      composite_id: compositeId,
      posture: String(currentComposite.posture || "day"),
      tts_voice: readCompositeField("tts_voice"),
      tts_language: readCompositeField("tts_language"),
      persona: this.querySelector(`[data-area-id="${CSS.escape(compositeId)}"][data-field-key="persona"]`)?.value || currentComposite.persona || "",
      persona_prompt: this.querySelector(`[data-area-id="${CSS.escape(compositeId)}"][data-field-key="persona_prompt"]`)?.value || "",
    });

    const status = this.querySelector(`.cg-composite-persona-status[data-composite-id="${CSS.escape(compositeId)}"]`);
    if (status) status.textContent = "Saving merged room...";
    try {
      await this._hass.callService("concierge", "update_composite_config", payload, undefined, true, true);
      this._clearActiveFormDraft();
      this._clearRoomPersonaDraft(compositeId);
      this._composites[compositeId] = { ...(this._composites[compositeId] || {}), ...payload };
      if (status) status.textContent = "Saved";
    } catch (err) {
      if (status) status.textContent = `Save failed: ${err?.message || err}`;
    }
  }

  async _saveRoomSection(areaId, section) {
    if (!areaId || !section) return;

    let payload = { area_id: areaId };
    if (section === "room_devices") {
      const deviceGroups = this._collectRoomDeviceGroups(areaId);
      payload = {
        ...payload,
        device_groups: deviceGroups,
      };
    } else if (section === "information_sources") {
      payload = {
        ...payload,
        ...this._buildInformationSourcesSectionPayload(areaId),
      };
    } else {
      return;
    }

    const status = this.querySelector(`.cg-room-status[data-area-id="${CSS.escape(areaId)}"]`);
    if (status) status.textContent = "Saving room section...";
    try {
      await this._hass.callService("concierge", "update_room_config", payload, undefined, true, true);
      this._rooms[areaId] = { ...(this._rooms[areaId] || {}), ...payload };
      if (this._selectedAreaId === areaId) {
        await this._loadActivityTimeline(false, areaId);
        this._openLatestRoomSaveDialog(areaId);
      }
      this._clearRoomSectionDraft(areaId, section);
      this._clearActiveFormDraft();
      if (status) status.textContent = "Saved";
    } catch (err) {
      if (status) status.textContent = `Save failed: ${err?.message || err}`;
    }
  }

  _cancelRoomSection(areaId, section) {
    if (!areaId || !section) return;
    this._clearRoomSectionDraft(areaId, section);
    this._clearActiveFormDraft();
    this._render();
  }

  _buildInformationSourcesSectionPayload(scopeId) {
    const selected = (fieldKey) => this._collectRoomSourceEntityIds(scopeId, fieldKey);
    const aiKnowledgeSwitch = this.querySelector(`[data-area-id="${CSS.escape(scopeId)}"][data-field-key="ai_knowledge_enabled"]`);
    return this._normalizeInformationSourcesPayload({
      ai_knowledge_enabled: Boolean(aiKnowledgeSwitch?.checked),
      weather_source_entity_ids: selected("weather_source_entity_ids"),
      news_source_entity_ids: selected("news_source_entity_ids"),
      asset_groups: this._collectRoomAssetGroups(scopeId),
      environment_information_outputs: selected("environment_information_outputs"),
    });
  }

  _renderInformationSourcesCards({
    scopeId,
    aiKnowledgeEnabled,
    weatherSourceEntityIds,
    newsSourceEntityIds,
    environmentInformationOutputs,
    assetRows,
    assetGroups,
    assetEmptyLabel,
    hasAssetIntelligence,
    canConfigureAi,
    canUseAssets,
  }) {
    const cards = [
      `<div class="cg-config-card" style="display:${canConfigureAi ? "block" : "none"};">
        <div class="cg-config-title">AI Knowledge</div>
        <div class="cg-muted">Enable general question and answer for this room using your configured AI source.</div>
        <div class="cg-switch-row" style="margin-top: 10px;">
          <span>Enable AI Knowledge</span>
          <ha-switch data-area-id="${this._escapeHtml(scopeId)}" data-field-key="ai_knowledge_enabled" data-room-section="information_sources" ${aiKnowledgeEnabled ? "checked" : ""}></ha-switch>
        </div>
      </div>`,
      this._renderRoomSourceEditor(scopeId, "weather_source_entity_ids", "Weather", this._globalSourceRowsForContext("weather"), weatherSourceEntityIds, "No global weather sources configured", true, "(drag into priority order)"),
      this._renderRoomSourceEditor(scopeId, "news_source_entity_ids", "News", this._globalSourceRowsForContext("news"), newsSourceEntityIds, "No global news sources configured", true, "(drag into priority order)"),
    ];

    if (hasAssetIntelligence && canUseAssets) {
      cards.push(this._renderRoomAssetGroupsEditor(scopeId, "Assets", assetRows, assetGroups, assetEmptyLabel));
      const environmentOptions = [
        { entity_id: "People Health", display_name: "People Health" },
        { entity_id: "Room Confidence", display_name: "Room Confidence" },
      ];
      cards.push(`
        <div class="cg-config-card">
          <div class="cg-config-title">Environment</div>
          <div class="cg-muted" style="margin-bottom: 10px;">Select whether to include People Health and Room Confidence informational outputs for this room.</div>
          ${this._renderRoomSourceEditor(scopeId, "environment_information_outputs", "Environment Outputs", environmentOptions, environmentInformationOutputs, "No environment outputs available", false)}
        </div>
      `);
    }

    return cards.join("");
  }

  async _saveCompositeSection(compositeId, section) {
    if (!compositeId || !section) return;

    let payload = { composite_id: compositeId };
    if (section === "room_devices") {
      const deviceGroups = this._collectRoomDeviceGroups(compositeId);
      const catalog = this._compositeCatalog?.[compositeId] || {};
      const fieldKeys = [
        "voice_device_entity_ids",
        "media_player_entity_ids",
        "speaker_entity_ids",
        "light_entity_ids",
        "shade_entity_ids",
        "room_sensor_entity_ids",
      ];
      const fieldSets = new Map(
        fieldKeys.map((fieldKey) => {
          const ids = new Set(
            (Array.isArray(catalog[fieldKey]) ? catalog[fieldKey] : [])
              .map((row) => String(row?.entity_id || "").trim())
              .filter(Boolean)
          );
          return [fieldKey, ids];
        })
      );
      const mappedPayload = {
        voice_device_entity_ids: [],
        media_player_entity_ids: [],
        speaker_entity_ids: [],
        light_entity_ids: [],
        shade_entity_ids: [],
        room_sensor_entity_ids: [],
      };
      const selectedEntityIds = Array.from(
        new Set(
          (Array.isArray(deviceGroups) ? deviceGroups : [])
            .flatMap((group) => this._roomDeviceGroupEntityIds(group))
        )
      );
      selectedEntityIds.forEach((entityId) => {
        fieldKeys.forEach((fieldKey) => {
          if (fieldSets.get(fieldKey)?.has(entityId)) {
            mappedPayload[fieldKey].push(entityId);
          }
        });
      });
      payload = {
        ...payload,
        device_groups: deviceGroups,
        ...mappedPayload,
      };
    } else if (section === "information_sources") {
      payload = {
        ...payload,
        ...this._buildInformationSourcesSectionPayload(compositeId),
      };
    } else {
      return;
    }

    const status = this.querySelector(`.cg-composite-status[data-composite-id="${CSS.escape(compositeId)}"]`);
    if (status) status.textContent = "Saving merged room section...";
    try {
      await this._hass.callService("concierge", "update_composite_config", payload, undefined, true, true);
      this._composites[compositeId] = { ...(this._composites[compositeId] || {}), ...payload };
      await this._load();
      this._clearRoomSectionDraft(compositeId, section);
      this._clearActiveFormDraft();
      this._render();
      // Some HA controls can emit a follow-up change event after rerender.
      // Apply a second clear on the next frame so section actions collapse reliably.
      window.requestAnimationFrame(() => {
        this._clearRoomSectionDraft(compositeId, section);
        this._updateRoomSectionDraftActions(compositeId);
      });
      if (status) status.textContent = "Saved";
    } catch (err) {
      if (status) status.textContent = `Save failed: ${err?.message || err}`;
    }
  }

  _cancelCompositeSection(compositeId, section) {
    if (!compositeId || !section) return;
    this._clearRoomSectionDraft(compositeId, section);
    this._clearActiveFormDraft();
    this._render();
  }

  async _savePersonProfile(personId) {
    const field = (fieldKey) => this.querySelector(`[data-person-id="${CSS.escape(personId)}"][data-field-key="${CSS.escape(fieldKey)}"]`);
    const readValue = (fieldKey) => {
      const el = field(fieldKey);
      if (!el) return "";

      const tagName = String(el.tagName || "").toUpperCase();
      if (tagName === "HA-SWITCH") return el.checked ? "true" : "false";
      if (tagName === "HA-AREA-PICKER") return String(el.value || "").trim();
      if (tagName === "SELECT") return String(el.value || "").trim();
      if (tagName === "HA-SELECT") {
        const selectedItem = el.querySelector("ha-list-item[selected], mwc-list-item[selected]");
        if (selectedItem) {
          return String(selectedItem.value || selectedItem.getAttribute("value") || "").trim();
        }
      }

      return String(el.value || "").trim();
    };
    const readList = (fieldKey) => {
      const el = field(fieldKey);
      if (!el) return [];

      const tagName = String(el.tagName || "").toUpperCase();
      if (tagName === "SELECT") {
        if (el.multiple) {
          return Array.from(el.selectedOptions || [])
            .map((item) => String(item.value || "").trim())
            .filter(Boolean);
        }
        const value = String(el.value || "").trim();
        return value ? [value] : [];
      }
      if (tagName === "HA-SELECT") {
        const selectedItems = Array.from(el.querySelectorAll("ha-list-item[selected], mwc-list-item[selected]"));
        const values = selectedItems
          .map((item) => String(item.value || item.getAttribute("value") || "").trim())
          .filter(Boolean);

        if (values.length) return values;

        const scalarValue = String(el.value || "").trim();
        return scalarValue ? [scalarValue] : [];
      }

      return String(el.value || "")
        .split(/\r?\n/)
        .map((item) => item.trim())
        .filter(Boolean);
    };
    const status = this.querySelector(`.cg-person-status[data-person-id="${CSS.escape(personId)}"]`);
    const person = this._peopleRegistry[personId] || {};
    const currentProfile = person?.profile && typeof person.profile === "object"
      ? person.profile
      : (this._people[personId] || {});
    let consent = currentProfile?.consent && typeof currentProfile.consent === "object"
      ? { ...currentProfile.consent }
      : {};

    const mobileNotifyTargets = readList("mobile_notify_targets");
    const preferredMobileTarget = readValue("preferred_mobile_target");
    const mobileVoiceEndpointEnabled = Boolean(field("mobile_voice_endpoint_enabled")?.checked);
    const stepUpMode = readValue("step_up_mode") || "app_confirmation";
    const stepUpPushConsentRequired = Boolean(field("step_up_push_consent_required")?.checked);
    const stepUpPinRequired = Boolean(field("step_up_pin_required")?.checked);

    const interactionTargets = consent.interaction_targets && typeof consent.interaction_targets === "object"
      ? consent.interaction_targets
      : {};
    const security = consent.security && typeof consent.security === "object"
      ? consent.security
      : {};
    const alarmStepUp = security?.alarm_step_up && typeof security.alarm_step_up === "object"
      ? security.alarm_step_up
      : {};
    const consentPolicyText = "By saving this profile, you confirm that person-level interaction policy and consent settings are being recorded for operational and safety controls.";
    const consentAcknowledged = Boolean(field("consent_acknowledged")?.checked);
    const existingAcknowledgedAt = String(consent.privacy_notice_acknowledged_at || "").trim();

    consent = {
      ...consent,
      interaction_targets: {
        ...interactionTargets,
        mobile_notify_targets: mobileNotifyTargets,
        preferred_mobile_target: preferredMobileTarget,
        mobile_voice_endpoint_enabled: mobileVoiceEndpointEnabled,
      },
      security: {
        ...security,
        alarm_step_up: {
          ...alarmStepUp,
          mode: stepUpMode,
          push_consent_required: stepUpPushConsentRequired,
          pin_required: stepUpPinRequired,
        },
      },
      privacy_notice_text: consentPolicyText,
      privacy_notice_acknowledged: consentAcknowledged,
      privacy_notice_acknowledged_at: consentAcknowledged
        ? (existingAcknowledgedAt || new Date().toISOString())
        : "",
    };

    const selectedIntentAbilities = readList("minor_allowed_intent_classes");
    const allowGeneralQna = selectedIntentAbilities.includes("general_qna");
    const allowedMinorIntentClasses = selectedIntentAbilities.filter((intentClass) => intentClass !== "general_qna");

    const currentName = String(currentProfile?.name || person?.name || personId || "").trim();

    const payload = this._normalizePersonProfilePayload({
      person_id: personId,
      name: readValue("name") || currentName,
      linked_area_id: readValue("linked_area_id") || undefined,
      voice_profile_id: readValue("voice_profile_id") || undefined,
      ble_device_ids: readList("ble_device_ids"),
      aqara_presence_entity_ids: readList("aqara_presence_entity_ids"),
      is_minor: Boolean(field("is_minor")?.checked),
      guardian_controls_required: Boolean(field("guardian_controls_required")?.checked),
      minor_allow_general_qna: allowGeneralQna,
      minor_allowed_intent_classes: allowedMinorIntentClasses,
      minor_content_filter_level: readValue("minor_content_filter_level") || "strict",
      consent,
      notes: field("notes")?.value || "",
    });

    if (status) status.textContent = "Saving person...";
    try {
      await this._hass.callService("concierge", "update_person_profile", payload, undefined, true, true);
      this._clearActiveFormDraft();
      if (status) status.textContent = "Saved";
      await this._load();
    } catch (err) {
      if (status) status.textContent = `Save failed: ${err?.message || err}`;
    }
  }

  _cancelPersonProfile() {
    this._clearActiveFormDraft();
    this._render();
  }

  _deriveVoiceProfileId(personId) {
    const normalized = String(personId || "")
      .trim()
      .toLowerCase()
      .replace(/[.\s]+/g, "_")
      .replace(/[^a-z0-9_-]/g, "");
    return `${normalized || "person"}_voice`;
  }

  _activeVoiceProfileIdForPerson(personId) {
    if (!personId) return "";
    const picker = this.querySelector(`[data-person-id="${CSS.escape(personId)}"][data-field-key="voice_profile_id"]`);
    const selectedInForm = this._readSelectControlValue(picker);
    if (selectedInForm) return selectedInForm;

    const profile = this._people?.[personId] || {};
    const personVoiceProfileId = String(profile.voice_profile_id || "").trim();
    if (personVoiceProfileId) return personVoiceProfileId;

    const derivedVoiceProfileId = this._deriveVoiceProfileId(personId);
    return this._voiceProfiles?.[derivedVoiceProfileId] ? derivedVoiceProfileId : "";
  }

  _setVoiceEnrollmentStatus(personId, text) {
    const status = this.querySelector(`.cg-voice-enrollment-status[data-person-id="${CSS.escape(personId)}"]`);
    if (status) status.textContent = text || "";
  }

  _setVoiceEnrollmentBusy(personId, isBusy, busyLabel = "") {
    const dialog = this._voiceEnrollmentDialog;
    if (!dialog?.open || dialog.personId !== personId) return;
    dialog.isBusy = Boolean(isBusy);
    dialog.busyLabel = dialog.isBusy ? String(busyLabel || "Working on your request...").trim() : "";
    this._render();
  }

  _voiceEnrollmentPhrases() {
    return CONCIERGE_VOICE_ENROLLMENT_CORPUS.map((item) => String(item.speech_text || "").trim());
  }

  async _fetchVoiceEnrollmentProgress(personId, voiceProfileId = "") {
    const query = new URLSearchParams({ person_id: personId });
    if (voiceProfileId) query.set("voice_profile_id", voiceProfileId);
    const response = await this._authFetch(`/api/concierge/voice_enrollment_progress?${query.toString()}`, 12000);
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `HTTP ${response.status}`);
    }
    return response.json();
  }

  async _refreshVoiceEnrollmentDialogProgress(personId, voiceProfileId = "") {
    const dialog = this._voiceEnrollmentDialog;
    if (!dialog?.open || dialog.personId !== personId) return;

    try {
      const progressResponse = await this._fetchVoiceEnrollmentProgress(personId, voiceProfileId || this._activeVoiceProfileIdForPerson(personId));
      if (!progressResponse?.found || !progressResponse?.progress) return;

      const progress = progressResponse.progress;
      const phrases = this._voiceEnrollmentPhrases();
      const maxPhraseIndex = Math.max(phrases.length - 1, 0);
      const sampleCount = Math.max(0, Number(progress.sample_count || 0));
      const targetSampleCount = Math.max(1, Number(progress.target_sample_count || phrases.length || 1));
      const completionPercentage = Math.max(0, Math.min(100, Number(progress.completion_percentage || 0)));
      const providerFromProgress = conciergeNormalizeVoiceEnrollmentProvider(progress.provider_type);
      const previousPhraseIndex = Math.max(0, Number(dialog.phraseIndex || 0));
      const localCaptureAwaitingAdvance = Boolean(dialog.currentCaptured);
      const highestCapturedPhraseIndex = Math.max(0, sampleCount - 1);
      const capturedPhraseIndices = Array.isArray(progress.captured_phrase_indices)
        ? progress.captured_phrase_indices.map((value) => Number(value)).filter((value) => Number.isFinite(value) && value >= 0)
        : [];
      const hasCapturedPhraseIndices = capturedPhraseIndices.length > 0;
      const capturedPhraseIndexSet = hasCapturedPhraseIndices ? new Set(capturedPhraseIndices.map((value) => Math.floor(value))) : null;

      if (progress.is_complete) {
        dialog.phraseIndex = Math.min(sampleCount, maxPhraseIndex);
        dialog.currentCaptured = true;
      } else if (highestCapturedPhraseIndex > previousPhraseIndex) {
        dialog.phraseIndex = Math.min(highestCapturedPhraseIndex, maxPhraseIndex);
        dialog.currentCaptured = true;
      } else if (localCaptureAwaitingAdvance && sampleCount >= previousPhraseIndex + 1) {
        dialog.phraseIndex = previousPhraseIndex;
        dialog.currentCaptured = true;
      } else if (sampleCount > previousPhraseIndex + 1) {
        dialog.phraseIndex = Math.min(sampleCount, maxPhraseIndex);
        dialog.currentCaptured = false;
      } else if (sampleCount <= previousPhraseIndex) {
        dialog.phraseIndex = Math.min(previousPhraseIndex, maxPhraseIndex);
        dialog.currentCaptured = false;
      } else {
        dialog.phraseIndex = Math.min(Math.max(sampleCount - 1, 0), maxPhraseIndex);
        dialog.currentCaptured = true;
      }
      if (capturedPhraseIndexSet) {
        const activePhraseIndex = Math.max(0, Math.min(Number(dialog.phraseIndex || 0), maxPhraseIndex));
        dialog.currentCaptured = capturedPhraseIndexSet.has(activePhraseIndex);
      }
      dialog.progress = progress;
      dialog.progressSummary = `${sampleCount}/${targetSampleCount} samples, ${completionPercentage}%`;
      dialog.enrollmentSessionId = String(progress.session_id || progressResponse.enrollment_session_id || dialog.enrollmentSessionId || "").trim();
      dialog.voiceProfileId = String(progressResponse.voice_profile_id || voiceProfileId || dialog.voiceProfileId || "").trim();
      if (providerFromProgress) {
        dialog.captureProvider = providerFromProgress;
      }

      try {
        const readinessResponse = await this._hass.callService(
          "concierge",
          "get_voice_enrollment_completion_readiness",
          {
            voice_profile_id: dialog.voiceProfileId,
            min_samples: CONCIERGE_VOICE_ENROLLMENT_MIN_ACCEPTED_UTTERANCES,
            min_total_duration_ms: CONCIERGE_VOICE_ENROLLMENT_MIN_TOTAL_DURATION_MS,
          },
          undefined,
          true,
          true
        );
        dialog.completionReadiness = this._normalizeVoiceEnrollmentReadiness(readinessResponse);
      } catch (err) {
        dialog.completionReadiness = null;
      }

      const summary = String(progress.user_safe_status_summary || "Enrollment in progress").trim() || "Enrollment in progress";
      dialog.status = `${summary} (${sampleCount}/${targetSampleCount}, ${completionPercentage}%)`;
      this._render();
    } catch (err) {
      // Keep existing dialog state on progress lookup failures.
    }
  }

  async _voiceEnrollmentRecoveryAction(action, personId, voiceProfileId = "") {
    const token = this._hass?.auth?.data?.access_token || "";
    const headers = {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };

    const response = await fetch("/api/concierge/voice_enrollment_recovery", {
      method: "POST",
      credentials: "same-origin",
      headers,
      body: JSON.stringify({
        action,
        person_id: personId,
        voice_profile_id: voiceProfileId,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async _captureVoiceEnrollmentRecording(personId, voiceProfileId, phraseIndex, speechText, recordingDurationMs, blob, promptMeta = {}) {
    const token = this._hass?.auth?.data?.access_token || "";
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const formData = new FormData();
    formData.append("person_id", personId);
    formData.append("voice_profile_id", voiceProfileId);
    formData.append("phrase_index", String(phraseIndex));
    formData.append("speech_text", speechText);
    formData.append("source", "guided_enrollment_dialog");
    formData.append("recording_duration_ms", String(Math.max(0, Number(recordingDurationMs) || 0)));
    if (promptMeta.prompt_id) formData.append("prompt_id", String(promptMeta.prompt_id));
    if (promptMeta.prompt_order !== undefined) formData.append("prompt_order", String(promptMeta.prompt_order));
    if (promptMeta.prompt_category) formData.append("prompt_category", String(promptMeta.prompt_category));
    if (promptMeta.prompt_length_bucket) formData.append("prompt_length_bucket", String(promptMeta.prompt_length_bucket));
    if (promptMeta.capture_distance) formData.append("capture_distance", String(promptMeta.capture_distance));
    if (promptMeta.capture_noise) formData.append("capture_noise", String(promptMeta.capture_noise));
    formData.append("quality_pass", "true");
    formData.append("audio", blob, `phrase_${String(phraseIndex + 1).padStart(2, "0")}.webm`);

    const response = await fetch("/api/concierge/voice_enrollment_capture", {
      method: "POST",
      credentials: "same-origin",
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `HTTP ${response.status}`);
    }

    return response.json();
  }

  _stopVoiceEnrollmentRecordingTracks() {
    const recording = this._voiceEnrollmentRecording;
    const stream = recording?.stream;
    if (stream && typeof stream.getTracks === "function") {
      stream.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch (err) {
          // no-op
        }
      });
    }
    recording.stream = null;
  }

  _hasActiveVoiceEnrollmentDialog() {
    return Boolean(this._voiceEnrollmentDialog?.open && this._voiceEnrollmentDialog?.personId);
  }

  _voiceEnrollmentBrowserCapability() {
    return conciergeGetBrowserVoiceEnrollmentCapability({
      isSecureContext: window?.isSecureContext,
      mediaDevices: navigator?.mediaDevices,
      MediaRecorderCtor: typeof MediaRecorder === "undefined" ? null : MediaRecorder,
    });
  }

  _voiceEnrollmentSatelliteOptions() {
    return conciergeCollectSatelliteOptions(this._hass?.states || {});
  }

  _normalizeVoiceEnrollmentReadiness(rawReadiness) {
    let readiness = rawReadiness;
    for (let depth = 0; depth < 3; depth += 1) {
      if (!readiness || typeof readiness !== "object") break;
      if (typeof readiness.ready === "boolean") break;
      if (readiness.response && typeof readiness.response === "object") {
        readiness = readiness.response;
        continue;
      }
      if (readiness.result && typeof readiness.result === "object") {
        readiness = readiness.result;
        continue;
      }
      if (readiness.readiness && typeof readiness.readiness === "object") {
        readiness = readiness.readiness;
        continue;
      }
      break;
    }
    return readiness && typeof readiness === "object" ? readiness : null;
  }

  _voiceEnrollmentCompletionStatus(dialog) {
    const readiness = dialog?.completionReadiness;
    if (!readiness) {
      const progress = dialog?.progress;
      const sampleCount = Math.max(0, Number(progress?.sample_count || 0));
      const targetSampleCount = Math.max(1, Number(progress?.target_sample_count || this._voiceEnrollmentPhrases().length || 1));
      if (sampleCount >= targetSampleCount && dialog?.currentCaptured) {
        return "Checking completion readiness...";
      }
      return "Capture the remaining phrases before building.";
    }
    if (readiness.ready) return "Ready to build voice profile.";
    const summary = String(readiness.user_safe_status_summary || "Not ready for completion.").trim() || "Not ready for completion.";
    const reasonCode = String(readiness.reason_code || "").trim();
    return reasonCode ? `${summary} [${reasonCode}]` : summary;
  }

  _applyVoiceEnrollmentDialogState(personId, seed = {}, render = false) {
    if (!personId) return this._voiceEnrollmentDialog;

    const activeVoiceProfileId = this._activeVoiceProfileIdForPerson(personId);
    const enrollmentProfile = activeVoiceProfileId ? this._voiceProfiles?.[activeVoiceProfileId] : null;
    const enrollmentConsent = enrollmentProfile?.consent?.voice_enrollment && typeof enrollmentProfile.consent.voice_enrollment === "object"
      ? enrollmentProfile.consent.voice_enrollment
      : {};
    const browserCapability = this._voiceEnrollmentBrowserCapability();
    const satelliteOptions = this._voiceEnrollmentSatelliteOptions();
    const previous = this._voiceEnrollmentDialog?.personId === personId ? this._voiceEnrollmentDialog : {};

    this._voiceEnrollmentDialog = conciergeBuildVoiceEnrollmentDialogState(previous, {
      open: true,
      personId,
      status: "Checking saved enrollment progress...",
      consentAcknowledged: Boolean(enrollmentConsent.consent_acknowledged),
      localOnly: enrollmentConsent.local_only !== false,
      captureProvider: conciergeResolveVoiceEnrollmentDefaultProvider({
        browserAvailable: browserCapability.available,
        satelliteCount: satelliteOptions.length,
      }),
      satelliteOptions,
      browserAvailable: browserCapability.available,
      browserSecureContext: browserCapability.secureContext,
      browserMicSupported: browserCapability.microphoneSupported,
      browserStatusSummary: browserCapability.summary,
      voiceProfileId: activeVoiceProfileId || this._deriveVoiceProfileId(personId),
      ...seed,
    });

    if (render) this._render();
    return this._voiceEnrollmentDialog;
  }

  _setVoiceEnrollmentCaptureProvider(personId, provider, { render = true } = {}) {
    const dialog = this._voiceEnrollmentDialog;
    if (!dialog?.open || dialog.personId !== personId) return dialog;

    const normalizedProvider = conciergeNormalizeVoiceEnrollmentProvider(provider)
      || conciergeResolveVoiceEnrollmentDefaultProvider({
        browserAvailable: dialog.browserAvailable,
        satelliteCount: Array.isArray(dialog.satelliteOptions) ? dialog.satelliteOptions.length : 0,
      });
    const availability = conciergeGetVoiceEnrollmentProviderAvailability({
      browserAvailable: dialog.browserAvailable,
      satelliteCount: Array.isArray(dialog.satelliteOptions) ? dialog.satelliteOptions.length : 0,
    });
    if (normalizedProvider === "browser" && !availability.browserSelectable) {
      return dialog;
    }
    if (normalizedProvider === "satellite" && !availability.satelliteSelectable) {
      return dialog;
    }

    if (
      normalizedProvider !== "browser"
      && this._voiceEnrollmentRecording?.active
      && this._voiceEnrollmentRecording?.personId === personId
      && this._voiceEnrollmentRecording?.recorder
      && this._voiceEnrollmentRecording.recorder.state !== "inactive"
    ) {
      try {
        this._voiceEnrollmentRecording.recorder.stop();
      } catch (err) {
        // no-op
      }
      this._stopVoiceEnrollmentRecordingTracks();
      this._voiceEnrollmentRecording = {
        active: false,
        personId: "",
        recorder: null,
        stream: null,
        startedAt: 0,
      };
    }

    dialog.captureProvider = normalizedProvider;
    dialog.showProviderFallback = false;
    if (normalizedProvider === "browser") {
      dialog.status = dialog.browserStatusSummary || dialog.status;
    } else if (Array.isArray(dialog.satelliteOptions) && dialog.satelliteOptions.length === 1 && !dialog.satelliteEntityId) {
      dialog.satelliteEntityId = dialog.satelliteOptions[0].entity_id;
      dialog.status = "Satellite capture selected. Choose the Voice Assistant device and capture the phrase.";
    } else if (normalizedProvider === "satellite") {
      dialog.status = dialog.satelliteEntityId
        ? "Satellite capture selected. Capture the phrase through the selected Voice Assistant device."
        : "Select a Voice Assistant device before capturing this phrase.";
    }
    if (render) this._render();
    return dialog;
  }

  _useVoiceEnrollmentSatelliteFallback(personId) {
    const dialog = this._setVoiceEnrollmentCaptureProvider(personId, "satellite", { render: false });
    if (!dialog) return;
    dialog.showProviderFallback = false;
    if (!dialog.satelliteEntityId && Array.isArray(dialog.satelliteOptions) && dialog.satelliteOptions.length === 1) {
      dialog.satelliteEntityId = dialog.satelliteOptions[0].entity_id;
    }
    dialog.status = dialog.satelliteEntityId
      ? "Voice Assistant Satellite selected. Capture the phrase through the selected device."
      : "Voice Assistant Satellite selected. Select a device before capturing this phrase.";
    this._render();
  }

  _browserVoiceEnrollmentFailureMessage(err) {
    const errorName = String(err?.name || "").trim();
    if (errorName === "NotAllowedError" || errorName === "PermissionDeniedError") {
      return "Microphone access was denied. Allow microphone access in the browser, or use Voice Assistant Satellite instead.";
    }
    if (errorName === "NotFoundError" || errorName === "DevicesNotFoundError") {
      return "No microphone was found for this browser session. Connect a microphone, or use Voice Assistant Satellite instead.";
    }
    if (errorName === "NotReadableError" || errorName === "TrackStartError") {
      return "This browser could not access the microphone. Close other apps using it, or use Voice Assistant Satellite instead.";
    }
    return `Capture failed: ${err?.message || err}`;
  }

  _openVoiceEnrollmentDialog(personId) {
    if (!personId) return;
    if (!this._integrationOptions?.capabilities?.cap_voice_enrollment) {
      const unavailableSummary = String(this._integrationOptions?.voice_enrollment_status_summary || "Voice enrollment is unavailable until integration prerequisites are met.").trim();
      this._setVoiceEnrollmentStatus(personId, unavailableSummary);
      return;
    }
    const dialog = this._applyVoiceEnrollmentDialogState(personId, {}, true);
    this._refreshVoiceEnrollmentDialogProgress(personId, dialog.voiceProfileId);
  }

  _closeVoiceEnrollmentDialog() {
    const recording = this._voiceEnrollmentRecording;
    if (recording?.active && recording.recorder && recording.recorder.state !== "inactive") {
      try {
        recording.recorder.stop();
      } catch (err) {
        // no-op
      }
    }
    this._stopVoiceEnrollmentRecordingTracks();
    this._voiceEnrollmentRecording = {
      active: false,
      personId: "",
      recorder: null,
      stream: null,
      startedAt: 0,
    };
    this._voiceEnrollmentDialog = conciergeBuildVoiceEnrollmentDialogState({}, {
      open: false,
      personId: "",
      phraseIndex: 0,
      currentCaptured: false,
      status: "",
      consentAcknowledged: false,
      localOnly: true,
      captureProvider: "browser",
      satelliteEntityId: "",
      satelliteOptions: [],
      browserAvailable: false,
      browserSecureContext: false,
      browserMicSupported: false,
      browserStatusSummary: "",
      progressSummary: "",
      progress: null,
      enrollmentSessionId: "",
      completionReadiness: null,
      showProviderFallback: false,
      voiceProfileId: "",
    });
    this._render();
  }

  async _cancelVoiceEnrollmentDialog(personId) {
    if (!personId) {
      this._closeVoiceEnrollmentDialog();
      return;
    }

    const voiceProfileId = this._activeVoiceProfileIdForPerson(personId) || "";
    const recording = this._voiceEnrollmentRecording;
    if (recording?.active && recording.recorder && recording.recorder.state !== "inactive") {
      try {
        recording.recorder.stop();
      } catch (err) {
        // no-op
      }
    }

    try {
      await this._voiceEnrollmentRecoveryAction("cancel", personId, voiceProfileId);
    } catch (err) {
      this._setVoiceEnrollmentStatus(personId, `Cancel failed: ${err?.message || err}`);
    }

    this._closeVoiceEnrollmentDialog();
    await this._load();
  }

  _syncVoiceEnrollmentDialogOptionsFromDom(personId) {
    const dialog = this._voiceEnrollmentDialog;
    if (!dialog?.open || dialog.personId !== personId) return dialog;

    const consentField = this.querySelector(`[data-person-id="${CSS.escape(personId)}"][data-voice-field="consent_acknowledged"]`);
    const localOnlyField = this.querySelector(`[data-person-id="${CSS.escape(personId)}"][data-voice-field="local_only"]`);
    const providerField = this.querySelector(`input[data-person-id="${CSS.escape(personId)}"][data-voice-field="capture_provider"]:checked`);
    const satelliteField = this.querySelector(`[data-person-id="${CSS.escape(personId)}"][data-voice-field="satellite_entity_id"]`);
    dialog.consentAcknowledged = Boolean(consentField?.checked);
    dialog.localOnly = localOnlyField ? Boolean(localOnlyField.checked) : true;
    dialog.captureProvider = conciergeNormalizeVoiceEnrollmentProvider(providerField?.value) || dialog.captureProvider || "browser";
    dialog.satelliteEntityId = String(satelliteField?.value || dialog.satelliteEntityId || "").trim();
    return dialog;
  }

  async _ensureVoiceEnrollmentStarted(personId) {
    if (!personId) return "";
    const dialog = this._syncVoiceEnrollmentDialogOptionsFromDom(personId);
    if (!dialog?.consentAcknowledged) {
      dialog.status = "Consent is required before enrollment can begin.";
      this._render();
      return "";
    }

    const person = this._peopleRegistry?.[personId] || {};
    const voiceProfileId = this._activeVoiceProfileIdForPerson(personId) || this._deriveVoiceProfileId(personId);
    await this._hass.callService(
      "concierge",
      "start_voice_enrollment",
      {
        person_id: personId,
        voice_profile_id: voiceProfileId,
        voice_name: `${String(person.name || personId)} Voice`,
        capture_provider: dialog.captureProvider || "browser",
        consent_acknowledged: true,
        local_only: dialog.localOnly !== false,
      },
      undefined,
      true,
      true
    );
    return voiceProfileId;
  }

  async _startVoiceEnrollment(personId) {
    if (!this._integrationOptions?.capabilities?.cap_voice_enrollment) {
      const unavailableSummary = String(this._integrationOptions?.voice_enrollment_status_summary || "Voice enrollment is unavailable until integration prerequisites are met.").trim();
      this._setVoiceEnrollmentStatus(personId, unavailableSummary);
      return;
    }
    this._ensureVoiceEnrollmentPersonView(personId);
    this._openVoiceEnrollmentDialog(personId);
    const activeVoiceProfileId = this._activeVoiceProfileIdForPerson(personId) || this._voiceEnrollmentDialog?.voiceProfileId || "";
    this._setVoiceEnrollmentBusy(personId, true, "Verifying enrollment session with backend...");
    try {
      const recovered = await this._voiceEnrollmentRecoveryAction("recover", personId, activeVoiceProfileId);
      if (recovered?.recovered && recovered?.progress) {
        if (this._voiceEnrollmentDialog?.open && this._voiceEnrollmentDialog.personId === personId) {
          this._voiceEnrollmentDialog.status = String(recovered.progress.user_safe_status_summary || "Enrollment recovered");
          this._voiceEnrollmentDialog.progress = recovered.progress;
          this._voiceEnrollmentDialog.enrollmentSessionId = String(recovered.session_id || this._voiceEnrollmentDialog.enrollmentSessionId || "").trim();
          this._render();
        }
        this._setVoiceEnrollmentStatus(personId, String(recovered.progress.user_safe_status_summary || "Enrollment recovered"));
      }
    } catch (err) {
      // Recovery lookup failures should not block opening enrollment dialog.
    } finally {
      this._setVoiceEnrollmentBusy(personId, false);
    }
    this._setVoiceEnrollmentBusy(personId, true, "Refreshing enrollment progress from backend...");
    try {
      await this._refreshVoiceEnrollmentDialogProgress(personId, activeVoiceProfileId);
    } finally {
      this._setVoiceEnrollmentBusy(personId, false);
    }
  }

  async _captureVoiceEnrollmentSample(personId) {
    if (!personId) return;
    const dialog = this._syncVoiceEnrollmentDialogOptionsFromDom(personId);
    if (!dialog?.open || dialog.personId !== personId) return;

    if (!this._archiveStatus?.destination_configured) {
      dialog.status = "Configure attached storage in Concierge integration options before recording voice enrollment samples.";
      this._render();
      return;
    }

    const phrases = this._voiceEnrollmentPhrases();
    const phraseIndex = Math.max(0, Math.min(dialog.phraseIndex, phrases.length - 1));
    const speechText = String(phrases[phraseIndex] || "").trim();
    const promptMeta = conciergeVoiceEnrollmentPrompt(phraseIndex);
    if (!speechText) return;

    if (dialog.captureProvider === "satellite") {
      if (!dialog.satelliteEntityId) {
        dialog.status = "Select a Voice Assistant device before capturing this phrase.";
        this._render();
        return;
      }

      dialog.showProviderFallback = false;
      dialog.status = "Capturing phrase through Voice Assistant Satellite...";
      this._render();
      this._setVoiceEnrollmentBusy(personId, true, "Capturing phrase and verifying backend status...");
      try {
        const voiceProfileId = await this._ensureVoiceEnrollmentStarted(personId);
        if (!voiceProfileId) return;

        const result = await this._hass.callService(
          "concierge",
          "capture_voice_enrollment_sample",
          {
            voice_profile_id: voiceProfileId,
            person_id: personId,
            speech_text: speechText,
            prompt_text: conciergeBuildSatelliteEnrollmentPrompt(phraseIndex, speechText),
            source: "guided_enrollment_dialog",
            phrase_index: phraseIndex,
            prompt_id: promptMeta.prompt_id,
            prompt_order: promptMeta.prompt_order,
            prompt_category: promptMeta.prompt_category,
            prompt_length_bucket: promptMeta.prompt_length_bucket,
            capture_distance: promptMeta.capture_distance,
            capture_noise: promptMeta.capture_noise,
            quality_pass: true,
            capture_provider: "satellite",
            satellite_entity_id: dialog.satelliteEntityId,
            timeout_seconds: 8.0,
          },
          undefined,
          true,
          true
        );

        const returnedSampleCount = Math.max(0, Number(result?.sample_count || 0));
        const reportedRegistered = Boolean(result?.sample_registered);
        const returnedCapturedPhraseIndices = Array.isArray(result?.captured_phrase_indices)
          ? result.captured_phrase_indices.map((value) => Number(value)).filter((value) => Number.isFinite(value) && value >= 0)
          : [];
        const returnedCapturedPhraseSet = returnedCapturedPhraseIndices.length > 0
          ? new Set(returnedCapturedPhraseIndices.map((value) => Math.floor(value)))
          : null;
        const observedRegistered = returnedCapturedPhraseSet
          ? returnedCapturedPhraseSet.has(phraseIndex)
          : returnedSampleCount >= phraseIndex + 1;
        if (!reportedRegistered && !observedRegistered) {
          const progressResponse = await this._fetchVoiceEnrollmentProgress(personId, voiceProfileId);
          const refreshedSampleCount = Math.max(0, Number(progressResponse?.progress?.sample_count || 0));
          const refreshedCapturedPhraseIndices = Array.isArray(progressResponse?.progress?.captured_phrase_indices)
            ? progressResponse.progress.captured_phrase_indices.map((value) => Number(value)).filter((value) => Number.isFinite(value) && value >= 0)
            : [];
          const refreshedCapturedPhraseSet = refreshedCapturedPhraseIndices.length > 0
            ? new Set(refreshedCapturedPhraseIndices.map((value) => Math.floor(value)))
            : null;
          const phraseConfirmedByProgress = refreshedCapturedPhraseSet
            ? refreshedCapturedPhraseSet.has(phraseIndex)
            : refreshedSampleCount >= phraseIndex + 1;
          if (phraseConfirmedByProgress) {
            dialog.currentCaptured = true;
            if (refreshedSampleCount > phraseIndex + 1) {
              dialog.phraseIndex = Math.min(refreshedSampleCount - 1, phrases.length - 1);
            }
            dialog.progressSummary = `${refreshedSampleCount}/${phrases.length} samples`;
            dialog.status = "Phrase captured. Click Next to continue.";
            dialog.voiceProfileId = voiceProfileId;
            await this._load();
            await this._refreshVoiceEnrollmentDialogProgress(personId, voiceProfileId);
            this._render();
            return;
          }

          const failureMessage = String(result?.failure_message_safe || result?.failure_code || "Satellite capture failed.").trim();
          dialog.status = failureMessage || "Satellite capture failed.";
          this._render();
          return;
        }

        dialog.currentCaptured = true;
        if (returnedSampleCount > phraseIndex + 1) {
          dialog.phraseIndex = Math.min(returnedSampleCount - 1, phrases.length - 1);
        }
        dialog.progressSummary = returnedSampleCount
          ? `${returnedSampleCount}/${phrases.length} samples`
          : dialog.progressSummary;
        dialog.status = "Phrase captured. Click Next to continue.";
        dialog.voiceProfileId = voiceProfileId;
        this._ensureVoiceEnrollmentPersonView(personId);
        await this._load();
        await this._refreshVoiceEnrollmentDialogProgress(personId, voiceProfileId);
        this._render();
      } catch (err) {
        dialog.status = `Capture failed: ${err?.message || err}`;
        this._render();
      } finally {
        this._setVoiceEnrollmentBusy(personId, false);
      }
      return;
    }

    if (!dialog.browserSecureContext) {
      dialog.status = dialog.browserStatusSummary;
      dialog.showProviderFallback = Array.isArray(dialog.satelliteOptions) && dialog.satelliteOptions.length > 0;
      this._render();
      return;
    }

    if (!dialog.browserMicSupported) {
      dialog.status = dialog.browserStatusSummary;
      dialog.showProviderFallback = Array.isArray(dialog.satelliteOptions) && dialog.satelliteOptions.length > 0;
      this._render();
      return;
    }

    const recording = this._voiceEnrollmentRecording;
    if (recording.active && recording.personId === personId && recording.recorder) {
      this._setVoiceEnrollmentBusy(personId, true, "Saving recording and verifying backend status...");
      dialog.status = "Saving recording...";
      this._render();
      try {
        recording.recorder.stop();
      } catch (err) {
        dialog.status = `Stop failed: ${err?.message || err}`;
        this._stopVoiceEnrollmentRecordingTracks();
        this._voiceEnrollmentRecording = {
          active: false,
          personId: "",
          recorder: null,
          stream: null,
          startedAt: 0,
        };
        this._setVoiceEnrollmentBusy(personId, false);
        this._render();
      }
      return;
    }

    dialog.status = "Requesting microphone access...";
    dialog.showProviderFallback = false;
    this._render();
    try {
      const voiceProfileId = await this._ensureVoiceEnrollmentStarted(personId);
      if (!voiceProfileId) return;

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const preferredMimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, preferredMimeType ? { mimeType: preferredMimeType } : undefined);
      const chunks = [];
      const startedAt = Date.now();

      recorder.addEventListener("dataavailable", (event) => {
        if (event.data && event.data.size > 0) {
          chunks.push(event.data);
        }
      });

      recorder.addEventListener("stop", async () => {
        const activeDialog = this._voiceEnrollmentDialog;
        try {
          const blob = new Blob(chunks, { type: recorder.mimeType || preferredMimeType || "audio/webm" });
          await this._captureVoiceEnrollmentRecording(
            personId,
            voiceProfileId,
            phraseIndex,
            speechText,
            Math.max(0, Date.now() - startedAt),
            blob,
            promptMeta
          );
          if (activeDialog?.open && activeDialog.personId === personId) {
            activeDialog.currentCaptured = true;
            activeDialog.status = "Phrase captured. Click Next to continue.";
          }
          this._ensureVoiceEnrollmentPersonView(personId);
          await this._load();
          await this._refreshVoiceEnrollmentDialogProgress(personId, voiceProfileId);
          this._render();
        } catch (err) {
          if (activeDialog?.open && activeDialog.personId === personId) {
            activeDialog.status = `Capture failed: ${err?.message || err}`;
            this._render();
          }
        } finally {
          this._stopVoiceEnrollmentRecordingTracks();
          this._voiceEnrollmentRecording = {
            active: false,
            personId: "",
            recorder: null,
            stream: null,
            startedAt: 0,
          };
          this._setVoiceEnrollmentBusy(personId, false);
          this._render();
        }
      }, { once: true });

      this._voiceEnrollmentRecording = {
        active: true,
        personId,
        recorder,
        stream,
        startedAt,
      };
      dialog.currentCaptured = false;
      dialog.status = "Recording... Read the sentence, then click End Record when you are done.";
      recorder.start();
      this._render();
    } catch (err) {
      dialog.status = this._browserVoiceEnrollmentFailureMessage(err);
      dialog.showProviderFallback = Array.isArray(dialog.satelliteOptions) && dialog.satelliteOptions.length > 0;
      this._stopVoiceEnrollmentRecordingTracks();
      this._voiceEnrollmentRecording = {
        active: false,
        personId: "",
        recorder: null,
        stream: null,
        startedAt: 0,
      };
      this._render();
    }
  }

  async _removeVoiceEnrollmentSample(personId, sampleId) {
    if (!personId || !sampleId) return;
    const voiceProfileId = this._activeVoiceProfileIdForPerson(personId);
    if (!voiceProfileId) return;

    this._setVoiceEnrollmentStatus(personId, "Removing speech item...");
    try {
      await this._hass.callService(
        "concierge",
        "remove_voice_enrollment_sample",
        { voice_profile_id: voiceProfileId, sample_id: sampleId },
        undefined,
        true,
        true
      );
      this._setVoiceEnrollmentStatus(personId, "Speech item removed.");
      await this._load();
    } catch (err) {
      this._setVoiceEnrollmentStatus(personId, `Remove failed: ${err?.message || err}`);
    }
  }

  async _buildVoiceProfile(personId, minSamples = CONCIERGE_VOICE_ENROLLMENT_MIN_ACCEPTED_UTTERANCES) {
    if (!personId) return;
    const voiceProfileId = this._activeVoiceProfileIdForPerson(personId);
    if (!voiceProfileId) {
      this._setVoiceEnrollmentStatus(personId, "Start enrollment first.");
      return;
    }

    this._setVoiceEnrollmentStatus(personId, "Building voice profile...");
    this._setVoiceEnrollmentBusy(personId, true, "Building voice profile and cleaning enrollment artifacts...");
    try {
      await this._hass.callService(
        "concierge",
        "complete_voice_enrollment",
        {
          voice_profile_id: voiceProfileId,
          person_id: personId,
          min_samples: minSamples,
          min_total_duration_ms: CONCIERGE_VOICE_ENROLLMENT_MIN_TOTAL_DURATION_MS,
        },
        undefined,
        true,
        true
      );
      if (this._voiceEnrollmentDialog?.open && this._voiceEnrollmentDialog.personId === personId) {
        this._voiceEnrollmentDialog.status = "Voice profile built.";
      }
      await this._load();
      this._closeVoiceEnrollmentDialog();
      this._setVoiceEnrollmentStatus(personId, "Voice profile built.");
    } catch (err) {
      if (this._voiceEnrollmentDialog?.open && this._voiceEnrollmentDialog.personId === personId) {
        this._voiceEnrollmentDialog.status = `Build failed: ${err?.message || err}`;
        this._render();
        return;
      }
      this._setVoiceEnrollmentStatus(personId, `Build failed: ${err?.message || err}`);
    } finally {
      this._setVoiceEnrollmentBusy(personId, false);
    }
  }

  async _advanceVoiceEnrollmentDialog(personId) {
    if (!personId) return;
    const dialog = this._voiceEnrollmentDialog;
    if (!dialog?.open || dialog.personId !== personId) return;
    const phrases = this._voiceEnrollmentPhrases();
    if (!dialog.currentCaptured) {
      dialog.status = "Record the phrase before moving to the next step.";
      this._render();
      return;
    }

    if (dialog.phraseIndex >= phrases.length - 1) {
      const voiceProfileId = this._activeVoiceProfileIdForPerson(personId);
      if (!voiceProfileId) {
        dialog.status = "Start enrollment first.";
        this._render();
        return;
      }

      try {
        this._setVoiceEnrollmentBusy(personId, true, "Checking completion readiness with backend...");
        const readinessResponse = await this._hass.callService(
          "concierge",
          "get_voice_enrollment_completion_readiness",
          {
            voice_profile_id: voiceProfileId,
            min_samples: CONCIERGE_VOICE_ENROLLMENT_MIN_ACCEPTED_UTTERANCES,
            min_total_duration_ms: CONCIERGE_VOICE_ENROLLMENT_MIN_TOTAL_DURATION_MS,
          },
          undefined,
          true,
          true
        );
        const readiness = this._normalizeVoiceEnrollmentReadiness(readinessResponse);
        if (!readiness?.ready) {
          dialog.completionReadiness = readiness;
          const statusSummary = String(readiness?.user_safe_status_summary || "Enrollment is not ready for completion.").trim();
          const readinessReason = String(readiness?.reason_code || "").trim();
          dialog.status = readinessReason ? `${statusSummary} [${readinessReason}]` : statusSummary;
          this._render();
          return;
        }
        dialog.completionReadiness = readiness;
      } catch (err) {
        dialog.status = `Readiness check failed: ${err?.message || err}`;
        this._render();
        return;
      } finally {
        this._setVoiceEnrollmentBusy(personId, false);
      }

      await this._buildVoiceProfile(personId, CONCIERGE_VOICE_ENROLLMENT_MIN_ACCEPTED_UTTERANCES);
      return;
    }

    dialog.phraseIndex += 1;
    dialog.currentCaptured = false;
    dialog.completionReadiness = null;
    dialog.status = "Read the next phrase naturally, then click Record Phrase.";
    this._render();
  }

  async _resetVoiceProfile(personId) {
    if (!personId) return;
    const voiceProfileId = this._activeVoiceProfileIdForPerson(personId);
    if (!voiceProfileId) {
      this._setVoiceEnrollmentStatus(personId, "No voice profile to reset.");
      return;
    }

    this._setVoiceEnrollmentStatus(personId, "Resetting voice profile...");
    try {
      await this._hass.callService(
        "concierge",
        "reset_voice_profile",
        { voice_profile_id: voiceProfileId, preserve_consent: true },
        undefined,
        true,
        true
      );
      this._setVoiceEnrollmentStatus(personId, "Voice profile reset.");
      await this._load();
    } catch (err) {
      this._setVoiceEnrollmentStatus(personId, `Reset failed: ${err?.message || err}`);
    }
  }

  async _deleteVoiceProfile(personId) {
    if (!personId) return;
    const voiceProfileId = this._activeVoiceProfileIdForPerson(personId);
    if (!voiceProfileId) {
      this._setVoiceEnrollmentStatus(personId, "No voice profile to delete.");
      return;
    }

    this._setVoiceEnrollmentStatus(personId, "Deleting voice profile...");
    try {
      await this._hass.callService(
        "concierge",
        "delete_voice_profile",
        { voice_profile_id: voiceProfileId, unlink_from_people: true },
        undefined,
        true,
        true
      );
      if (this._voiceEnrollmentDialog?.open && this._voiceEnrollmentDialog.personId === personId) {
        this._closeVoiceEnrollmentDialog();
      }
      this._setVoiceEnrollmentStatus(personId, "Voice profile deleted.");
      await this._load();
    } catch (err) {
      this._setVoiceEnrollmentStatus(personId, `Delete failed: ${err?.message || err}`);
    }
  }

  _syncPersonIntentAbilityField(personId) {
    if (!personId) return;
    const hiddenField = this.querySelector(`[data-person-id="${CSS.escape(personId)}"][data-field-key="minor_allowed_intent_classes"]`);
    if (!hiddenField) return;

    const selectedIntentClasses = Array.from(this.querySelectorAll(`.cg-person-intent-item[data-person-id="${CSS.escape(personId)}"]`))
      .map((item) => String(item.getAttribute("data-intent-class") || "").trim())
      .filter(Boolean);

    hiddenField.value = selectedIntentClasses.join("\n");
  }

  _applyPersonIntentAbility(personId, intentClass) {
    if (!personId || !intentClass) return;
    const list = this.querySelector(`.cg-person-intent-list[data-person-id="${CSS.escape(personId)}"]`);
    if (!list) return;

    const existing = list.querySelector(`.cg-person-intent-item[data-intent-class="${CSS.escape(intentClass)}"]`);
    if (existing) return;

    const picker = this.querySelector(`[data-person-id="${CSS.escape(personId)}"][data-field-key="minor_intent_ability_picker"]`);
    const label = this._readSelectControlLabel(picker) || intentClass;

    const row = document.createElement("div");
    row.className = "cg-selected-source cg-person-intent-item";
    row.setAttribute("data-person-id", personId);
    row.setAttribute("data-intent-class", intentClass);
    row.innerHTML = `
      <div class="cg-selected-source-label">
        <div class="cg-selected-source-text">
          <div class="cg-selected-source-primary">${this._escapeHtml(label)}</div>
          <div class="cg-selected-source-secondary">Intent Ability</div>
        </div>
      </div>
      <ha-button class="cg-remove-source cg-person-remove-intent" appearance="plain" data-person-id="${this._escapeHtml(personId)}" data-intent-class="${this._escapeHtml(intentClass)}">Remove</ha-button>
    `;

    const empty = list.querySelector(".cg-selected-empty");
    if (empty) empty.style.display = "none";
    list.append(row);

    const removeButton = row.querySelector(".cg-person-remove-intent");
    if (removeButton) {
      removeButton.addEventListener("click", () => {
        this._removePersonIntentAbility(personId, intentClass);
      });
    }

    this._syncPersonIntentAbilityField(personId);
    this._syncPersonIntentAbilityPicker(personId);
    this._markActiveFormDraftDirty();
  }

  _removePersonIntentAbility(personId, intentClass) {
    if (!personId || !intentClass) return;
    const list = this.querySelector(`.cg-person-intent-list[data-person-id="${CSS.escape(personId)}"]`);
    if (!list) return;

    const row = list.querySelector(`.cg-person-intent-item[data-intent-class="${CSS.escape(intentClass)}"]`);
    if (row) row.remove();

    const empty = list.querySelector(".cg-selected-empty");
    if (empty) {
      empty.style.display = list.querySelector(".cg-person-intent-item") ? "none" : "block";
    }

    this._syncPersonIntentAbilityField(personId);
    this._syncPersonIntentAbilityPicker(personId);
    this._markActiveFormDraftDirty();
  }

  _bindEvents() {
    this.querySelectorAll("ha-entity-picker[data-allowed-entity-ids]").forEach((picker) => {
      try {
        picker.hass = this._hass;
      } catch (err) {
        // no-op
      }

      try {
        const allowed = JSON.parse(picker.getAttribute("data-allowed-entity-ids") || "[]");
        const allowedSet = new Set(Array.isArray(allowed) ? allowed.filter(Boolean) : []);
        picker.includeEntities = Array.from(allowedSet);
        picker.entityFilter = (candidate) => {
          if (typeof candidate === "string") return allowedSet.has(candidate);
          if (candidate && typeof candidate === "object") {
            const entityId = String(
              candidate.entity_id
                || candidate.entityId
                || candidate?.stateObj?.entity_id
                || ""
            ).trim();
            return allowedSet.has(entityId);
          }
          return false;
        };
      } catch (err) {
        // no-op
      }

      if (picker.value === undefined || picker.value === null) {
        try {
          picker.value = "";
        } catch (err) {
          // no-op
        }
      }

      if (typeof picker.requestUpdate === "function") {
        try {
          picker.requestUpdate();
        } catch (err) {
          // no-op
        }
      }
    });

    this.querySelectorAll("ha-select[data-field-key]").forEach((selectControl) => {
      try {
        selectControl.hass = this._hass;
      } catch (err) {
        // no-op
      }

      try {
        const rawOptions = selectControl.getAttribute("data-options-json") || "[]";
        selectControl.options = JSON.parse(rawOptions);
      } catch (err) {
        // no-op
      }

      try {
        selectControl.value = selectControl.getAttribute("data-current-value") || "";
      } catch (err) {
        // no-op
      }

      try {
        selectControl.label = selectControl.getAttribute("data-label") || "";
      } catch (err) {
        // no-op
      }

      try {
        selectControl.required = false;
        selectControl.clearable = true;
      } catch (err) {
        // no-op
      }

      if (typeof selectControl.requestUpdate === "function") {
        try {
          selectControl.requestUpdate();
        } catch (err) {
          // no-op
        }
      }
    });

    this.querySelectorAll("ha-labels-picker, ha-label-picker").forEach((picker) => {
      try {
        picker.hass = this._hass;
      } catch (err) {
        // no-op
      }

      try {
        picker._labels = this._labelRegistry || [];
      } catch (err) {
        // no-op
      }

      if (typeof picker.requestUpdate === "function") {
        try {
          picker.requestUpdate();
        } catch (err) {
          // no-op
        }
      }

      if (picker.getAttribute("data-cg-asset-sync-bound") !== "1") {
        picker.setAttribute("data-cg-asset-sync-bound", "1");
        const syncAssetGroups = () => {
          const fieldKey = String(picker.getAttribute("data-field-key") || "");
          const areaId = String(picker.getAttribute("data-area-id") || "");
          if (fieldKey !== "asset_groups" || !areaId) return;

          this._markActiveFormDraftDirty(`room:${areaId}`);
          this._markRoomSectionDraftDirty(areaId, this._roomSectionForFieldKey("asset_groups"));
          this._syncRoomAssetGroupDeviceOptions(areaId);
          setTimeout(() => this._syncRoomAssetGroupDeviceOptions(areaId), 0);
        };

        picker.addEventListener("value-changed", syncAssetGroups);
        picker.addEventListener("change", syncAssetGroups);
      }
    });

    this.querySelectorAll("ha-device-picker").forEach((picker) => {
      try {
        picker.hass = this._hass;
      } catch (err) {
        // no-op
      }

      const allowedRaw = picker.getAttribute("data-allowed-device-ids") || "[]";
      let allowed = [];
      try {
        allowed = JSON.parse(allowedRaw);
      } catch (err) {
        allowed = [];
      }

      if (Array.isArray(allowed) && allowed.length) {
        const allowedSet = new Set(allowed.filter(Boolean));
        try {
          picker.deviceFilter = (candidate) => {
            if (typeof candidate === "string") return allowedSet.has(candidate);
            if (candidate && typeof candidate === "object") {
              const deviceId = String(candidate.id || candidate.device_id || "").trim();
              return allowedSet.has(deviceId);
            }
            return false;
          };
        } catch (err) {
          // no-op
        }
      }
    });

    this.querySelectorAll("ha-area-picker[data-field-key]").forEach((picker) => {
      try {
        picker.hass = this._hass;
      } catch (err) {
        // no-op
      }

      const initialValue = picker.getAttribute("data-initial-value") || "";
      if (!picker.value || picker.value === "") {
        picker.value = initialValue;
      }
    });

    this._applyLabelRegistryToPickers(this);

    this.querySelectorAll(".cg-asset-groups[data-area-id]").forEach((groupList) => {
      const areaId = groupList.getAttribute("data-area-id") || "";
      if (areaId) {
        this._syncRoomAssetGroupDeviceOptions(areaId);
      }
    });

    this.querySelectorAll(".cg-device-groups[data-area-id]").forEach((groupList) => {
      const areaId = groupList.getAttribute("data-area-id") || "";
      if (areaId) {
        this._syncRoomDeviceGroupEntityOptions(areaId);
      }
    });

    this.querySelectorAll("button[data-nav='home']").forEach((button) => {
      button.addEventListener("click", () => this._goHome());
    });

    this.querySelectorAll("button[data-nav-room]").forEach((button) => {
      const areaId = button.getAttribute("data-nav-room");
      button.addEventListener("click", () => {
        if (areaId) this._openRoom(areaId);
      });
    });

    this.querySelectorAll("[data-open-global-settings]").forEach((button) => {
      button.addEventListener("click", () => this._openGlobalSettingsDialog());
    });

    this.querySelectorAll("[data-close-global-settings]").forEach((button) => {
      button.addEventListener("click", () => this._closeGlobalSettingsDialog());
    });

    this.querySelectorAll("[data-save-global-settings]").forEach((button) => {
      button.addEventListener("click", () => this._saveGlobalSettings({ closeOnSuccess: true }));
    });

    this.querySelectorAll("[data-global-settings-dialog]").forEach((dialog) => {
      dialog.addEventListener("closed", () => {
        this._globalSettingsDialogOpen = false;
      });
    });

    this.querySelectorAll("[data-edit-merge-dialog]").forEach((dialog) => {
      dialog.addEventListener("closed", () => this._closeEditMergeDialog());
    });

    this.querySelectorAll("[data-activity-detail-dialog]").forEach((dialog) => {
      dialog.addEventListener("closed", () => this._closeActivityDetails());
    });

    const globalSaveButton = this.querySelector(".cg-save-global");
    if (globalSaveButton) {
      globalSaveButton.addEventListener("click", () => this._saveGlobalSettings());
    }

    const exportArchiveButton = this.querySelector(".cg-export-archive");
    if (exportArchiveButton) {
      exportArchiveButton.addEventListener("click", () => this._exportActivityArchive());
    }

    this.querySelectorAll("[data-activity-filter]").forEach((button) => {
      button.addEventListener("click", () => {
        const nextFilter = String(button.getAttribute("data-activity-filter") || "all").toLowerCase();
        this._activityTimelineFilter = nextFilter || "all";
        this._render();
      });
    });

    const activitySearchInput = this.querySelector("#cg-activity-search");
    if (activitySearchInput) {
      activitySearchInput.addEventListener("input", () => {
        this._activityTimelineSearch = activitySearchInput.value || "";
        this._render();
      });
    }

    this.querySelectorAll(".cg-add-source").forEach((button) => {
      button.addEventListener("click", () => {
        const contextType = button.getAttribute("data-context-type") || "";
        const areaId = button.getAttribute("data-area-id") || "";
        const fieldKey = button.getAttribute("data-field-key") || "";
        const selectId = button.getAttribute("data-source-select-id") || "";
        if (!selectId) return;

        const select = this.querySelector(`#${CSS.escape(selectId)}`);
        if (!select) return;

        const selectedValue = this._readSelectControlValue(select);
        if (!selectedValue) return;

        let valueMap = {};
        try {
          valueMap = JSON.parse(select.getAttribute("data-source-value-map") || "{}");
        } catch (err) {
          valueMap = {};
        }
        const entityId = String(valueMap[selectedValue] || selectedValue || "").trim();
        if (!entityId) return;

        let detailsMap = {};
        try {
          detailsMap = JSON.parse(select.getAttribute("data-source-details-map") || "{}");
        } catch (err) {
          detailsMap = {};
        }
        let sourceInfo = detailsMap[selectedValue] || detailsMap[entityId] || null;

        if (areaId && fieldKey) {
          const selectedIds = this._collectRoomSourceEntityIds(areaId, fieldKey);
          if (selectedIds.includes(entityId)) return;

          let label = "";
          try {
            const labelMap = JSON.parse(select.getAttribute("data-label-map") || "{}");
            label = String(labelMap[selectedValue] || "").trim();
          } catch (err) {
            label = "";
          }
          label = label || this._readSelectControlLabel(select) || entityId;
          sourceInfo = sourceInfo || this._sourceInfoFromLabel(entityId, label);
          const list = this.querySelector(`.cg-room-selected[data-area-id="${CSS.escape(areaId)}"][data-field-key="${CSS.escape(fieldKey)}"]`);
          if (!list) return;

          list.insertAdjacentHTML(
            "beforeend",
            this._renderRoomSelectedSourceRow(
              areaId,
              fieldKey,
              entityId,
              sourceInfo,
              this._isRoomSourceReorderable(fieldKey)
            )
          );
          select.value = "";
          this._markActiveFormDraftDirty(`room:${areaId}`);
          const section = this._roomSectionForFieldKey(fieldKey);
          if (section) this._markRoomSectionDraftDirty(areaId, section);
          this._syncRoomSelectedEmptyState(areaId, fieldKey);
          this._syncSourcePickerAvailability(select, this._collectRoomSourceEntityIds(areaId, fieldKey));
          return;
        }

        if (!contextType) return;

        const selectedIds = this._collectGlobalSourceEntityIds(contextType);
        if (selectedIds.includes(entityId)) return;

        let label = "";
        try {
          const labelMap = JSON.parse(select.getAttribute("data-label-map") || "{}");
          label = String(labelMap[selectedValue] || "").trim();
        } catch (err) {
          label = "";
        }
        label = label || this._readSelectControlLabel(select) || entityId;
        sourceInfo = sourceInfo || this._sourceInfoFromLabel(entityId, label);
        const list = this.querySelector(`.cg-selected-sources[data-context-type="${CSS.escape(contextType)}"]`);
        if (!list) return;

        list.insertAdjacentHTML("beforeend", this._renderSelectedSourceRow(contextType, entityId, sourceInfo));
        select.value = "";
        this._markActiveFormDraftDirty("global");
        this._syncSelectedSourceEmptyState(contextType);
        this._syncSourcePickerAvailability(select, this._collectGlobalSourceEntityIds(contextType));
      });
    });

    this.querySelectorAll(".cg-selected-sources").forEach((list) => {
      list.addEventListener("click", (event) => {
        const target = event.target instanceof Element ? event.target : null;
        const removeButton = target?.closest(".cg-remove-source");
        if (!removeButton) return;

        const row = removeButton.closest(".cg-selected-source");
        if (!row) return;

        const contextType = list.getAttribute("data-context-type") || "";
        const areaId = list.getAttribute("data-area-id") || "";
        const fieldKey = list.getAttribute("data-field-key") || "";
        row.remove();
        if (areaId && fieldKey) {
          this._markActiveFormDraftDirty(`room:${areaId}`);
          const section = this._roomSectionForFieldKey(fieldKey);
          if (section) this._markRoomSectionDraftDirty(areaId, section);
          this._syncRoomSelectedEmptyState(areaId, fieldKey);
          const roomSelectId = this._roomSourceSelectId(areaId, fieldKey);
          const roomSelect = this.querySelector(`#${CSS.escape(roomSelectId)}`);
          if (roomSelect) {
            this._syncSourcePickerAvailability(roomSelect, this._collectRoomSourceEntityIds(areaId, fieldKey));
          }
        } else {
          this._markActiveFormDraftDirty("global");
          this._syncSelectedSourceEmptyState(contextType);
          const globalSelectId = `cg-${contextType}-source-select`;
          const globalSelect = this.querySelector(`#${CSS.escape(globalSelectId)}`);
          if (globalSelect) {
            this._syncSourcePickerAvailability(globalSelect, this._collectGlobalSourceEntityIds(contextType));
          }
        }
      });
    });

    this.querySelectorAll('.cg-room-selected-item[data-reorderable="true"]').forEach((item) => {
      item.addEventListener("dragstart", (event) => {
        const source = event.currentTarget;
        if (!(source instanceof Element)) return;
        event.dataTransfer?.setData("text/plain", source.getAttribute("data-source-entity-id") || "");
        source.classList.add("cg-dragging");
      });

      item.addEventListener("dragend", (event) => {
        const source = event.currentTarget;
        if (source instanceof Element) source.classList.remove("cg-dragging");
      });

      item.addEventListener("dragover", (event) => {
        event.preventDefault();
      });

      item.addEventListener("drop", (event) => {
        event.preventDefault();
        const target = event.currentTarget;
        if (!(target instanceof Element)) return;

        const list = target.closest(".cg-room-selected");
        const dragging = list?.querySelector('.cg-room-selected-item.cg-dragging[data-reorderable="true"]');
        if (!list || !dragging || dragging === target) return;

        const targetRect = target.getBoundingClientRect();
        const before = event.clientY < (targetRect.top + targetRect.height / 2);
        list.insertBefore(dragging, before ? target : target.nextSibling);

        const areaId = target.getAttribute("data-area-id") || "";
        const fieldKey = target.getAttribute("data-field-key") || "";
        if (areaId && fieldKey) {
          this._markActiveFormDraftDirty(`room:${areaId}`);
          const section = this._roomSectionForFieldKey(fieldKey);
          if (section) this._markRoomSectionDraftDirty(areaId, section);
        }
      });
    });

    this.querySelectorAll(".cg-open-room").forEach((button) => {
      button.addEventListener("click", () => {
        const areaId = button.getAttribute("data-area-id");
        if (areaId) this._openRoom(areaId);
      });
    });

    this.querySelectorAll(".cg-room-click").forEach((card) => {
      const areaId = card.getAttribute("data-area-id");
      card.addEventListener("click", () => {
        if (areaId) this._openRoom(areaId);
      });
      card.addEventListener("keydown", (event) => {
        if ((event.key === "Enter" || event.key === " ") && areaId) {
          event.preventDefault();
          this._openRoom(areaId);
        }
      });
    });

    this.querySelectorAll(".cg-person-click").forEach((card) => {
      const personId = card.getAttribute("data-person-id");
      card.addEventListener("click", () => {
        if (personId) this._openPerson(personId);
      });
      card.addEventListener("keydown", (event) => {
        if ((event.key === "Enter" || event.key === " ") && personId) {
          event.preventDefault();
          this._openPerson(personId);
        }
      });
    });

    this.querySelectorAll(".cg-merge-room").forEach((checkbox) => {
      checkbox.addEventListener("click", (event) => {
        event.stopPropagation();
        this._mergeLog("checkbox click", { value: checkbox.value, checked: checkbox.checked });
      });
      checkbox.addEventListener("change", (event) => {
        event.stopPropagation();
        this._mergeLog("checkbox change", { value: checkbox.value, checked: checkbox.checked });
        this._syncMergeSelectionForCheckbox(event.currentTarget || checkbox);
      });
    });

    this.querySelectorAll(".cg-merge-pick").forEach((label) => {
      label.addEventListener("click", (event) => {
        event.stopPropagation();
      });
    });

    const mergeNameInput = this.querySelector("#cg-merge-name");
    if (mergeNameInput) {
      mergeNameInput.addEventListener("input", () => {
        this._mergeDraftName = mergeNameInput.value || "";
        this._renderMergeStatus();
      });
      mergeNameInput.addEventListener("click", (event) => {
        event.stopPropagation();
      });
    }

    this.querySelectorAll(".cg-room-link").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const areaId = link.getAttribute("data-area-id");
        if (areaId) this._openRoom(areaId);
      });
    });

    this.querySelectorAll(".cg-composite-click").forEach((card) => {
      const compositeId = card.getAttribute("data-composite-id");
      card.addEventListener("click", () => {
        if (compositeId) this._openComposite(compositeId);
      });
      card.addEventListener("keydown", (event) => {
        if ((event.key === "Enter" || event.key === " ") && compositeId) {
          event.preventDefault();
          this._openComposite(compositeId);
        }
      });
    });

    this.querySelectorAll(".cg-composite-link").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const compositeId = link.getAttribute("data-composite-id");
        if (compositeId) this._openComposite(compositeId);
      });
    });

    this.querySelectorAll(".cg-edit-merge-open").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const compositeId = button.getAttribute("data-composite-id");
        if (compositeId) this._openEditMergeDialog(compositeId);
      });
    });

    const editMergeNameInput = this.querySelector("#cg-edit-merge-name");
    if (editMergeNameInput) {
      editMergeNameInput.addEventListener("input", () => {
        this._editMergeName = editMergeNameInput.value || "";
      });
      editMergeNameInput.addEventListener("click", (event) => {
        event.stopPropagation();
      });
    }

    this.querySelectorAll(".cg-edit-merge-room").forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        this._editMergeError = "";
        this._syncEditMergeSelectionFromDom();
      });
    });

    const editMergeCancelButton = this.querySelector("[data-edit-merge-cancel]");
    if (editMergeCancelButton) {
      editMergeCancelButton.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        this._closeEditMergeDialog();
      });
    }

    const editMergeCloseButton = this.querySelector("[data-edit-merge-close]");
    if (editMergeCloseButton) {
      editMergeCloseButton.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        this._closeEditMergeDialog();
      });
    }

    const editMergeUpdateButton = this.querySelector("[data-edit-merge-update]");
    if (editMergeUpdateButton) {
      editMergeUpdateButton.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        this._saveEditMergeDialog();
      });
    }

    const backButton = this.querySelector(".cg-back-home");
    if (backButton) {
      backButton.addEventListener("click", () => this._goHome());
    }

    this.querySelectorAll(".cg-save-person").forEach((button) => {
      button.addEventListener("click", () => {
        const personId = button.getAttribute("data-person-id");
        if (personId) this._savePersonProfile(personId);
      });
    });

    this.querySelectorAll(".cg-cancel-person").forEach((button) => {
      button.addEventListener("click", () => {
        this._cancelPersonProfile();
      });
    });

    this.querySelectorAll(".cg-person-begin-enrollment").forEach((button) => {
      button.addEventListener("click", () => {
        const personId = button.getAttribute("data-person-id") || "";
        if (personId) this._startVoiceEnrollment(personId);
      });
    });

    this.querySelectorAll(".cg-person-voice-dialog-close").forEach((button) => {
      button.addEventListener("click", () => {
        const personId = button.getAttribute("data-person-id") || this._voiceEnrollmentDialog?.personId || "";
        this._cancelVoiceEnrollmentDialog(personId);
      });
    });

    this.querySelectorAll('[data-voice-field="consent_acknowledged"], [data-voice-field="local_only"]').forEach((field) => {
      field.addEventListener("change", () => {
        const personId = field.getAttribute("data-person-id") || this._voiceEnrollmentDialog?.personId || "";
        const dialog = personId ? this._syncVoiceEnrollmentDialogOptionsFromDom(personId) : null;
        if (!personId || !dialog?.open || dialog.personId !== personId) return;

        if (!conciergeIsVoiceEnrollmentAuthorized(dialog)) {
          dialog.status = "Check both authorization boxes to enable capture method, phrase workflow, and completion controls.";
        } else if (dialog.captureProvider === "satellite" && !dialog.satelliteEntityId) {
          dialog.status = "Select a Voice Assistant device before capturing this phrase.";
        } else if (dialog.captureProvider === "satellite") {
          dialog.status = "Capture transport and phrase workflow are now available.";
        } else {
          dialog.status = dialog.browserStatusSummary || "Capture transport and phrase workflow are now available.";
        }

        this._render();
      });
    });

    this.querySelectorAll('input[data-voice-field="capture_provider"]').forEach((field) => {
      field.addEventListener("change", () => {
        const personId = field.getAttribute("data-person-id") || this._voiceEnrollmentDialog?.personId || "";
        if (personId) this._setVoiceEnrollmentCaptureProvider(personId, field.value, { render: true });
      });
    });

    this.querySelectorAll('[data-voice-field="satellite_entity_id"]').forEach((field) => {
      field.addEventListener("change", () => {
        const personId = field.getAttribute("data-person-id") || this._voiceEnrollmentDialog?.personId || "";
        const dialog = this._voiceEnrollmentDialog;
        if (!personId || !dialog?.open || dialog.personId !== personId) return;
        dialog.satelliteEntityId = String(field.value || "").trim();
        dialog.status = dialog.satelliteEntityId
          ? "Voice Assistant device selected. Capture the phrase when ready."
          : "Select a Voice Assistant device before capturing this phrase.";
        this._render();
      });
    });

    this.querySelectorAll(".cg-person-voice-provider-fallback").forEach((button) => {
      button.addEventListener("click", () => {
        const personId = button.getAttribute("data-person-id") || this._voiceEnrollmentDialog?.personId || "";
        if (personId) this._useVoiceEnrollmentSatelliteFallback(personId);
      });
    });

    this.querySelectorAll(".cg-person-record-voice-phrase").forEach((button) => {
      button.addEventListener("click", () => {
        const personId = button.getAttribute("data-person-id") || "";
        if (personId) this._captureVoiceEnrollmentSample(personId);
      });
    });

    this.querySelectorAll(".cg-person-next-voice-phrase").forEach((button) => {
      button.addEventListener("click", () => {
        const personId = button.getAttribute("data-person-id") || "";
        if (personId) this._advanceVoiceEnrollmentDialog(personId);
      });
    });

    this.querySelectorAll(".cg-person-delete-voice").forEach((button) => {
      button.addEventListener("click", () => {
        const personId = button.getAttribute("data-person-id") || "";
        if (personId) this._deleteVoiceProfile(personId);
      });
    });

    this.querySelectorAll(".cg-apply-ble-suggestions").forEach((button) => {
      button.addEventListener("click", () => {
        const personId = button.getAttribute("data-person-id");
        if (!personId) return;
        const person = this._peopleRegistry[personId];
        const suggestions = Array.isArray(person?.ble_device_suggestions) ? person.ble_device_suggestions : [];
        const field = this.querySelector(`[data-person-id="${CSS.escape(personId)}"][data-field-key="ble_device_ids"]`);
        if (field) {
          field.value = suggestions.join("\n");
          this._markActiveFormDraftDirty(`person:${personId}`);
        }
      });
    });

    this.querySelectorAll(".cg-person-add-intent").forEach((button) => {
      button.addEventListener("click", () => {
        const personId = button.getAttribute("data-person-id") || "";
        if (!personId) return;
        const picker = this.querySelector(`[data-person-id="${CSS.escape(personId)}"][data-field-key="minor_intent_ability_picker"]`);
        const intentClass = this._readSelectControlValue(picker);
        this._applyPersonIntentAbility(personId, intentClass);
      });
    });

    this.querySelectorAll(".cg-person-remove-intent").forEach((button) => {
      button.addEventListener("click", () => {
        const personId = button.getAttribute("data-person-id") || "";
        const intentClass = button.getAttribute("data-intent-class") || "";
        this._removePersonIntentAbility(personId, intentClass);
      });
    });

    this.querySelectorAll(".cg-save-room-persona").forEach((button) => {
      button.addEventListener("click", () => {
        const areaId = button.getAttribute("data-area-id");
        if (areaId) this._saveRoomPersona(areaId);
      });
    });

    this.querySelectorAll(".cg-save-composite-persona").forEach((button) => {
      button.addEventListener("click", () => {
        const compositeId = button.getAttribute("data-composite-id");
        if (compositeId) this._saveCompositePersona(compositeId);
      });
    });

    this.querySelectorAll(".cg-room-section-save").forEach((button) => {
      button.addEventListener("click", () => {
        const areaId = button.getAttribute("data-area-id") || "";
        const section = button.getAttribute("data-room-section") || "";
        if (areaId && section) this._saveRoomSection(areaId, section);
      });
    });

    this.querySelectorAll(".cg-room-section-cancel").forEach((button) => {
      button.addEventListener("click", () => {
        const areaId = button.getAttribute("data-area-id") || "";
        const section = button.getAttribute("data-room-section") || "";
        if (areaId && section) this._cancelRoomSection(areaId, section);
      });
    });

    this.querySelectorAll(".cg-composite-section-save").forEach((button) => {
      button.addEventListener("click", () => {
        const compositeId = button.getAttribute("data-composite-id") || "";
        const section = button.getAttribute("data-room-section") || "";
        if (compositeId && section) this._saveCompositeSection(compositeId, section);
      });
    });

    this.querySelectorAll(".cg-composite-section-cancel").forEach((button) => {
      button.addEventListener("click", () => {
        const compositeId = button.getAttribute("data-composite-id") || "";
        const section = button.getAttribute("data-room-section") || "";
        if (compositeId && section) this._cancelCompositeSection(compositeId, section);
      });
    });

    this.querySelectorAll(".cg-listen-room-persona").forEach((button) => {
      button.addEventListener("click", () => {
        const areaId = button.getAttribute("data-area-id");
        if (areaId) this._openRoomVoiceDialog(areaId);
      });
    });

    this.querySelectorAll("[data-room-voice-close]").forEach((button) => {
      button.addEventListener("click", () => this._closeRoomVoiceDialog());
    });

    this.querySelectorAll("[data-room-voice-dialog]").forEach((dialog) => {
      dialog.addEventListener("closed", () => this._closeRoomVoiceDialog());
    });

    this.querySelectorAll("[data-room-voice-play]").forEach((button) => {
      button.addEventListener("click", () => {
        const areaId = button.getAttribute("data-area-id");
        if (areaId) this._listenRoomPersona(areaId);
      });
    });

    this.querySelectorAll(".cg-activity-item").forEach((item) => {
      item.addEventListener("click", () => {
        const areaId = item.getAttribute("data-area-id") || "";
        const activityId = item.getAttribute("data-activity-id") || "";
        if (areaId && activityId) this._openActivityDetails(areaId, activityId);
      });
    });

    this.querySelectorAll("[data-activity-detail-close]").forEach((button) => {
      button.addEventListener("click", () => this._closeActivityDetails());
    });

    this.querySelectorAll(".cg-save-composite").forEach((button) => {
      button.addEventListener("click", () => {
        const compositeId = button.getAttribute("data-composite-id");
        if (compositeId) this._saveCompositeConfig(compositeId);
      });
    });

    const mergeToggleButton = this.querySelector(".cg-toggle-merge");
    if (mergeToggleButton) {
      mergeToggleButton.addEventListener("click", () => {
        this._mergeMode = !this._mergeMode;
        if (!this._mergeMode) {
          this._mergeDraftName = "";
          this._mergeDraftAreaIds = [];
        }
        this._render();
      });
    }

    const mergeCreateButton = this.querySelector(".cg-create-composite");
    if (mergeCreateButton) {
      mergeCreateButton.addEventListener("click", () => this._createCompositeFromSelection());
    }

    this.querySelectorAll("[data-panel-reload]").forEach((button) => {
      button.addEventListener("click", () => {
        this._reloadPanelPage();
      });
    });

    this.querySelectorAll("[data-panel-dismiss]").forEach((button) => {
      button.addEventListener("click", () => {
        this._panelVersionDismissed = true;
        this._render();
      });
    });

    if (this._selectedAreaId) {
      this._updateRoomSectionDraftActions(this._selectedAreaId);
    }
    if (this._selectedCompositeId) {
      this._updateRoomSectionDraftActions(this._selectedCompositeId);
    }
  }

  _renderStartupLoading() {
    this.innerHTML = `
      <style>
        .cg-shell { padding: 24px; font-family: var(--primary-font-family); color: var(--primary-text-color); }
        .cg-head { display: flex; align-items: center; gap: 16px; margin-bottom: 22px; }
        .cg-logo { height: 34px; width: 34px; object-fit: contain; }
        .cg-title { font-size: 24px; font-weight: 700; }
        .cg-subtitle { opacity: 0.72; margin-top: 4px; }
        .cg-card { border-radius: 16px; padding: 18px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,0.08)); }
      </style>
      <div class="cg-shell">
        ${this._renderPanelUpdateBanner()}
        <div class="cg-head">
          <img class="cg-logo" src="${this._logoSrc()}" alt="Concierge">
          <div>
            <div class="cg-title">Concierge</div>
            <div class="cg-subtitle">Loading your configuration...</div>
          </div>
        </div>
        <div class="cg-card">Loading room, device, and integration data.</div>
      </div>
    `;
  }

  _renderMain() {
    if (!this._activityTimelineLoaded && !this._activityTimelineLoading) {
      this._loadActivityTimeline(false);
    }

    const floorMap = {};
    this._floors.forEach((floor) => {
      if (floor && floor.floor_id) floorMap[floor.floor_id] = floor;
    });

    const grouped = {};
    for (const area of this._areas) {
      const floorId = area?.floor_id || null;
      const floorName = String(
        (floorId && floorMap[floorId] ? floorMap[floorId].name : "")
        || area?.floor_name
        || "Unassigned"
      );
      if (!grouped[floorName]) grouped[floorName] = [];
      grouped[floorName].push(area);
    }

    const floorOrder = Object.keys(grouped).sort((a, b) => String(a).localeCompare(String(b)));

    const weatherCfg = this._mergedGlobalConfig("weather");
    const newsCfg = this._mergedGlobalConfig("news");
    const alarmCfg = this._mergedGlobalConfig("alarm_status");

    const weatherSourceEntityIds = Array.isArray(weatherCfg?.options?.source_entity_ids)
      ? weatherCfg.options.source_entity_ids.filter(Boolean)
      : [];
    const newsSourceEntityIds = Array.isArray(newsCfg?.options?.source_entity_ids)
      ? newsCfg.options.source_entity_ids.filter(Boolean)
      : [];
    const alarmEntityId = alarmCfg?.options?.entity_id || "";
    const archiveStatus = this._archiveStatus || {};
    const archiveDestinationConfigured = Boolean(archiveStatus.destination_configured);
    const archiveDestinationUri = String(archiveStatus.destination_uri || "");
    const archiveEnabled = Boolean(archiveStatus.archive_enabled);
    const archiveIncludeRefs = Boolean(archiveStatus.include_reference_excerpts);
    const haPurgeKeepDays = Math.max(1, Number(archiveStatus.ha_purge_keep_days || 10));
    const archiveCaptureAgeDays = Math.max(1, Number(archiveStatus.archive_capture_age_days || Math.max(1, haPurgeKeepDays - 2)));
    const archiveRetentionDays = Math.max(1, Number(archiveStatus.archive_retention_days || 30));
    const archiveEnabledMessage = `Audit Archive is enabled and will archive history that is ${archiveCaptureAgeDays} days old before Home Assistant purges history at ${haPurgeKeepDays} days.`;
    const archiveDisabledMessage = `Audit Archive is NOT enabled and all archive history will be purged after ${haPurgeKeepDays} days following the normal Home Assistant cleanup process. If you want longer retention, enable Audit Archive in the integration setup gear.`;
    const integrationOptions = this._integrationOptions || {};
    const capabilityFlags = integrationOptions.capabilities || {};
    const aiSummary = capabilityFlags.cap_ai
      ? `Enabled via ${integrationOptions.action_provider || "configured provider"}`
      : "Disabled (enable AI and action provider in integration gear)";
    const ttsSummary = capabilityFlags.cap_tts
      ? `${integrationOptions.tts_provider || "configured provider"}`
      : "Disabled";
    const assetSummary = capabilityFlags.cap_assets
      ? "Enabled via integration gear link"
      : "Disabled (Asset Intelligence not linked in integration gear)";
    const voiceEnrollmentSummary = capabilityFlags.cap_voice_enrollment
      ? "Enabled"
      : "Disabled (requires archive destination + archive enabled)";
    const weatherRows = Array.isArray(this._globalCatalog.weather_entity_ids) ? this._globalCatalog.weather_entity_ids : [];
    const newsRows = Array.isArray(this._globalCatalog.news_entity_ids) ? this._globalCatalog.news_entity_ids : [];
    const weatherMap = new Map(weatherRows.map((row) => [String(row?.entity_id || ""), String(row?.display_name || row?.name || row?.entity_id || "")]));
    const newsMap = new Map(newsRows.map((row) => [String(row?.entity_id || ""), String(row?.display_name || row?.name || row?.entity_id || "")]));
    const weatherSummary = weatherSourceEntityIds.length
      ? weatherSourceEntityIds.slice(0, 2).map((entityId) => weatherMap.get(entityId) || entityId).join(", ")
      : "Not configured";
    const newsSummary = newsSourceEntityIds.length
      ? newsSourceEntityIds.slice(0, 2).map((entityId) => newsMap.get(entityId) || entityId).join(", ")
      : "Not configured";
    const alarmSummary = alarmEntityId ? this._friendlyEntityName(alarmEntityId) : "Not configured";
    const globalSettingsDialogMarkup = this._renderGlobalSettingsDialog(weatherSourceEntityIds, newsSourceEntityIds, alarmEntityId);
    const people = Object.values(this._peopleRegistry || {}).sort((left, right) => String(left?.name || left?.entity_id || "").localeCompare(String(right?.name || right?.entity_id || "")));
    const peopleMarkup = people.length
      ? people.map((person) => {
          const personId = person.entity_id || "";
          const profile = this._people[personId] || {};
          const interactionTargets = profile?.consent?.interaction_targets && typeof profile.consent.interaction_targets === "object"
            ? profile.consent.interaction_targets
            : {};
          const mobileTargets = Array.isArray(interactionTargets.mobile_notify_targets)
            ? interactionTargets.mobile_notify_targets
            : [];
          const mobileVoiceEndpointEnabled = Boolean(interactionTargets.mobile_voice_endpoint_enabled);
          const voiceProfile = profile.voice_profile_id ? this._voiceProfiles[profile.voice_profile_id] : null;
          const voiceLabel = voiceProfile?.name || profile.voice_profile_id || "Not set";
          const voiceEnrollmentState = String(voiceProfile?.enrollment_state || "untrained").trim() || "untrained";
          const voiceSampleCount = Number(voiceProfile?.sample_count || 0);
          const deviceTrackers = Array.isArray(person.device_trackers) ? person.device_trackers : [];
          const inZones = Array.isArray(person.in_zones) ? person.in_zones : [];
          const entityPicture = this._personImage(person);
          return `
            <div class="cg-room-card cg-person-click" data-person-id="${this._escapeHtml(personId)}" role="button" tabindex="0" aria-label="Open profile for ${this._escapeHtml(person.name || personId)}">
              ${entityPicture ? `<img class="cg-room-image" src="${this._escapeHtml(entityPicture)}" alt="${this._escapeHtml(person.name || personId)}">` : ""}
              <div class="cg-room-head">
                <div class="cg-room-name">${this._escapeHtml(person.name || personId)}</div>
              </div>
              <div class="cg-room-meta">State: ${this._escapeHtml(person.state || "unknown")}</div>
              <div class="cg-room-meta">Tracked devices: ${deviceTrackers.length}</div>
              <div class="cg-room-meta">In zones: ${inZones.length}</div>
              <div class="cg-room-meta">Voice profile: ${this._escapeHtml(voiceLabel)}</div>
              <div class="cg-room-meta">Voice enrollment: ${this._escapeHtml(voiceEnrollmentState)}</div>
              <div class="cg-room-meta">Voice samples: ${this._escapeHtml(String(voiceSampleCount))}</div>
              <div class="cg-room-meta">Mobile targets: ${this._escapeHtml(String(mobileTargets.length))}</div>
              <div class="cg-room-meta">Mobile voice endpoint: ${this._escapeHtml(mobileVoiceEndpointEnabled ? "Enabled" : "Disabled")}</div>
            </div>
          `;
        }).join("")
      : `<div class="cg-muted">No people profiles have been created yet.</div>`;

    const enabledComposites = Object.values(this._composites || {})
      .filter((item) => item && item.enabled !== false && Array.isArray(item.area_ids) && item.area_ids.length > 0);
    const memberAreaIds = new Set(enabledComposites.flatMap((item) => item.area_ids || []));

    const compositesByFloor = {};
    enabledComposites.forEach((composite) => {
      const firstAreaId = (composite.area_ids || [])[0];
      const firstArea = this._areas.find((area) => area.id === firstAreaId);
      const compositeFloorId = composite.floor_id || firstArea?.floor_id || null;
      const floorName = compositeFloorId && floorMap[compositeFloorId]
        ? floorMap[compositeFloorId].name
        : "Unassigned";
      if (!compositesByFloor[floorName]) compositesByFloor[floorName] = [];
      compositesByFloor[floorName].push(composite);
    });

    const roomsMarkup = floorOrder.map((floorName) => {
      const roomCards = grouped[floorName]
        .filter((area) => !memberAreaIds.has(area.id))
        .sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")))
        .map((area) => {
          const room = this._rooms[area.id] || {};
          const roomFloorLabel = String(
            area.floor_name
            || (area.floor_id && floorMap[area.floor_id] ? floorMap[area.floor_id].name : "")
            || "Unassigned"
          );
          const availableCards = this._availableRoomCards(this._roomCatalog[area.id] || {});
          const configuredCount = this._configuredCardCount(room, availableCards);
          const totalCount = availableCards.length;
          const voiceAssistantId = (room.voice_device_entity_ids || [])[0] || "";
          const primarySpeakerId = (room.speaker_entity_ids || room.media_player_entity_ids || [])[0] || "";
          const voiceAssistant = voiceAssistantId ? this._friendlyEntityName(voiceAssistantId) : "Not set";
          const primarySpeaker = primarySpeakerId ? this._friendlyEntityName(primarySpeakerId) : "Not set";
          const persona = room.persona || "Not set";
          const isConfigured = configuredCount > 0;
          const statusLine = totalCount
            ? `Configured ${configuredCount} of ${totalCount} categories`
            : "No configurable integrations detected";
          const cardImage = area.picture
            ? `<img class="cg-room-image" src="${this._escapeHtml(area.picture)}" alt="${this._escapeHtml(area.name || area.id)}">`
            : "";
          const mergeCheckbox = this._mergeMode
            ? `<label class="cg-merge-pick cg-merge-pick-inline"><input class="cg-merge-room" type="checkbox" value="${this._escapeHtml(area.id)}" data-floor-id="${this._escapeHtml(area.floor_id || "")}"${this._mergeDraftAreaIds.includes(area.id) ? " checked" : ""}><span>Merge</span></label>`
            : "";

          return `
            <div class="cg-room-card cg-room-click" data-area-id="${this._escapeHtml(area.id)}" role="button" tabindex="0" aria-label="Open configuration for ${this._escapeHtml(area.name || area.id)}">
              ${cardImage}
              <div class="cg-room-head">
                <div class="cg-room-name">${this._escapeHtml(area.name || area.id)}</div>
                ${mergeCheckbox}
              </div>
              <div class="cg-room-meta">${this._escapeHtml(statusLine)}</div>
              <div class="cg-room-meta">Voice Assistant: ${this._escapeHtml(voiceAssistant)}</div>
              <div class="cg-room-meta">Primary Speakers: ${this._escapeHtml(primarySpeaker)}</div>
              <div class="cg-room-meta">Persona: ${this._escapeHtml(persona)}</div>
              <div class="cg-room-meta">Floor: ${this._escapeHtml(roomFloorLabel)}</div>
              <div class="cg-row-end" style="margin-top: 8px;">
                <a href="#" class="cg-room-link" data-area-id="${this._escapeHtml(area.id)}">${isConfigured ? "Open room configuration" : "Configure room"}</a>
              </div>
            </div>
          `;
        })
        .join("");

      const compositeCards = (compositesByFloor[floorName] || [])
        .sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")))
        .map((composite) => {
          const compositeId = composite.composite_id || "";
          const memberNames = this._memberAreaNames(composite.area_ids || []);
          const memberLabel = memberNames.length ? memberNames.join(", ") : "No member rooms";
          const catalog = this._compositeCatalog[compositeId] || {};
          const availableCards = this._availableRoomCards(catalog);
          const totalCount = availableCards.length;
          const configuredCount = this._configuredCardCount(composite, availableCards);
          const voiceAssistantId = (composite.voice_device_entity_ids || [])[0] || "";
          const primarySpeakerId = (composite.speaker_entity_ids || composite.media_player_entity_ids || [])[0] || "";
          const voiceAssistant = voiceAssistantId ? this._friendlyEntityName(voiceAssistantId) : "Not set";
          const primarySpeaker = primarySpeakerId ? this._friendlyEntityName(primarySpeakerId) : "Not set";
          const statusLine = totalCount
            ? `Configured ${configuredCount} of ${totalCount} categories`
            : "No configurable integrations detected";

          return `
            <div class="cg-room-card cg-composite-click" data-composite-id="${this._escapeHtml(compositeId)}" role="button" tabindex="0" aria-label="Open configuration for ${this._escapeHtml(composite.name || compositeId)}">
              <div class="cg-room-head">
                <div class="cg-room-name">${this._escapeHtml(composite.name || compositeId)}</div>
                <button type="button" class="cg-room-action cg-edit-merge-open" data-composite-id="${this._escapeHtml(compositeId)}">Edit Merge</button>
              </div>
              <div class="cg-room-meta">Rooms: ${this._escapeHtml(memberLabel)}</div>
              <div class="cg-room-meta">${this._escapeHtml(statusLine)}</div>
              <div class="cg-room-meta">Voice Assistant: ${this._escapeHtml(voiceAssistant)}</div>
              <div class="cg-room-meta">Primary Speakers: ${this._escapeHtml(primarySpeaker)}</div>
              <div class="cg-room-meta">Persona: Composite context</div>
              <div class="cg-row-end" style="margin-top: 8px;">
                <a href="#" class="cg-composite-link" data-composite-id="${this._escapeHtml(compositeId)}">Open room configuration</a>
              </div>
            </div>
          `;
        })
        .join("");

      const cards = `${compositeCards}${roomCards}`;
      const editMergeDialog = this._renderEditMergeDialog();
      return `
        <div class="cg-floor-section">
          <div class="cg-floor-title">${this._escapeHtml(floorName)}</div>
          <div class="cg-grid">${cards}</div>
        </div>
        ${editMergeDialog}
      `;
    }).join("");

    this.innerHTML = `
      <style>
        .cg-shell { padding: 24px; font-family: var(--primary-font-family); color: var(--primary-text-color); }
        .cg-head { display: flex; align-items: center; gap: 16px; margin-bottom: 18px; }
        .cg-logo { height: 34px; width: 34px; object-fit: contain; }
        .cg-title { font-size: 24px; font-weight: 700; }
        .cg-subtitle { opacity: 0.72; margin-top: 4px; }
        .cg-breadcrumb { font-size: 14px; margin-bottom: 12px; font-weight: 400; color: var(--secondary-text-color); padding: 8px 12px; border-radius: 10px; background: color-mix(in srgb, var(--card-background-color) 88%, var(--primary-color) 12%); }
        .cg-breadcrumb button { appearance: none; border: none; background: transparent; padding: 0; margin: 0; font: inherit; color: var(--secondary-text-color); cursor: pointer; text-decoration: underline; }
        .cg-breadcrumb-current { font-size: 14px; font-weight: 600; color: var(--primary-text-color); }
        .cg-settings-summary { border-radius: 16px; padding: 18px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,0.08)); margin-bottom: 16px; }
        .cg-settings-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
        .cg-settings-title { font-size: 16px; font-weight: 700; }
        .cg-settings-copy { color: var(--secondary-text-color); font-size: 13px; margin-top: 4px; }
        .cg-settings-gear-btn { --mdc-theme-primary: var(--primary-color); }
        .cg-settings-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin-top: 12px; }
        .cg-settings-item { border: 1px solid var(--divider-color); border-radius: 12px; padding: 10px; background: var(--ha-card-background, var(--card-background-color)); }
        .cg-settings-item-label { font-size: 12px; color: var(--secondary-text-color); }
        .cg-settings-item-value { font-size: 13px; color: var(--primary-text-color); margin-top: 4px; line-height: 1.4; }
        .cg-global { border-radius: 16px; padding: 18px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,0.08)); margin-bottom: 16px; }
        .cg-global-title { font-size: 16px; font-weight: 600; margin-bottom: 6px; }
        .cg-global-copy { color: var(--secondary-text-color); font-size: 13px; }
        .cg-global-grid { display: grid; gap: 12px; margin-top: 12px; }
        .cg-global-item label { display: block; font-size: 13px; color: var(--secondary-text-color); margin-bottom: 4px; }
        .cg-global-item select { min-height: 36px; width: 100%; }
        .cg-source-picker-row { --cg-source-action-width: 52px; --cg-source-gap: 8px; display: grid; grid-template-columns: minmax(0, 1fr) var(--cg-source-action-width); gap: var(--cg-source-gap); align-items: center; }
        .cg-source-picker-row ha-select { width: 100%; }
        .cg-add-source { --mdc-theme-primary: var(--primary-color); }
        .cg-add-source { width: var(--cg-source-action-width, 52px); justify-self: end; }
        .cg-add-source[disabled] { opacity: 0.55; }
        .cg-selected-sources { display: grid; gap: 6px; margin-top: 8px; }
        .cg-source-selection-list { margin-right: calc(var(--cg-source-action-width, 52px) + var(--cg-source-gap, 8px)); }
        .cg-selected-source { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 10px; border-radius: 10px; padding: 8px 0 8px 10px; background: var(--ha-card-background, var(--card-background-color)); border: 1px solid var(--divider-color); }
        .cg-selected-source-label { display: flex; align-items: center; gap: 6px; min-width: 0; }
        .cg-selected-source-text { min-width: 0; }
        .cg-selected-source-primary { font-size: 13px; color: var(--primary-text-color); line-height: 1.3; }
        .cg-selected-source-secondary { font-size: 11px; color: var(--secondary-text-color); line-height: 1.25; margin-top: 1px; }
        .cg-remove-source { justify-self: end; margin: 0; border-radius: 999px; background: color-mix(in srgb, var(--error-color) 16%, transparent); color: var(--error-color); --mdc-theme-primary: var(--error-color); --mdc-button-horizontal-padding: 10px; }
        .cg-selected-empty { font-size: 12px; color: var(--secondary-text-color); }
        .cg-archive-status { font-size: 12px; color: var(--secondary-text-color); }
        .cg-rooms-title { font-size: 18px; font-weight: 700; margin: 14px 0 10px; }
        .cg-floor-section { margin-bottom: 18px; }
        .cg-floor-title { font-size: 15px; font-weight: 700; margin: 8px 0 10px; }
        .cg-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
        .cg-room-card { border-radius: 16px; padding: 14px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,0.08)); }
        .cg-room-click { cursor: pointer; border: 1px solid transparent; transition: transform 0.12s ease, border-color 0.12s ease; }
        .cg-room-click:hover { transform: translateY(-1px); border-color: var(--primary-color); }
        .cg-room-click:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 28%, transparent); }
        .cg-room-image { width: 100%; height: 120px; object-fit: cover; border-radius: 12px; margin-bottom: 10px; }
        .cg-room-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; margin-bottom: 6px; }
        .cg-room-name { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
        .cg-room-action { border: 0; border-radius: 10px; padding: 6px 10px; background: color-mix(in srgb, var(--primary-color) 14%, transparent); color: var(--primary-color); cursor: pointer; font-weight: 700; font-size: 12px; white-space: nowrap; }
        .cg-room-action:hover { background: color-mix(in srgb, var(--primary-color) 22%, transparent); }
        .cg-merge-pick-inline { display: inline-flex; align-items: center; gap: 4px; margin-top: 2px; white-space: nowrap; }
        .cg-merge-pick-inline span { font-size: 12px; color: var(--secondary-text-color); }
        .cg-room-meta { font-size: 13px; color: var(--secondary-text-color); line-height: 1.45; }
        .cg-row-end { display: flex; align-items: center; gap: 10px; margin-top: 12px; }
        .cg-merge-pick { display: block; margin-top: 8px; font-size: 12px; color: var(--secondary-text-color); }
        .cg-merge-pick input { margin-right: 6px; }
        .cg-modal-backdrop { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 24px; background: rgba(0, 0, 0, 0.42); }
        .cg-modal { width: min(640px, 100%); border-radius: 18px; padding: 18px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 16px 48px rgba(0, 0, 0, 0.24)); }
        .cg-modal-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
        .cg-modal-title { font-size: 18px; font-weight: 800; }
        .cg-modal-copy { font-size: 13px; color: var(--secondary-text-color); margin-top: 4px; }
        .cg-modal-close { border: 0; background: transparent; cursor: pointer; color: var(--secondary-text-color); font-size: 24px; line-height: 1; }
        .cg-modal-body { display: grid; gap: 14px; }
        .cg-modal-field { display: grid; gap: 6px; }
        .cg-modal-field > span { font-size: 13px; font-weight: 600; color: var(--primary-text-color); }
        .cg-modal-field input { min-height: 36px; width: 100%; }
        .cg-edit-merge-list { display: grid; gap: 8px; max-height: 240px; overflow: auto; padding: 4px 2px; }
        .cg-edit-merge-item { display: flex; align-items: center; gap: 10px; font-size: 14px; color: var(--primary-text-color); }
        .cg-edit-merge-item input { width: 16px; height: 16px; margin: 0; }
        .cg-modal-hint { font-size: 12px; color: var(--secondary-text-color); }
        .cg-modal-error { min-height: 18px; font-size: 12px; color: var(--error-color); }
        .cg-modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
        .cg-modal-cancel, .cg-modal-update { border: 0; border-radius: 10px; padding: 8px 14px; cursor: pointer; font-weight: 700; }
        .cg-modal-cancel { background: color-mix(in srgb, var(--primary-text-color) 8%, transparent); color: var(--primary-text-color); }
        .cg-modal-update { background: var(--primary-color); color: #fff; }
        .cg-open-room, .cg-save-global { border: 0; border-radius: 10px; padding: 8px 12px; background: var(--primary-color); color: #fff; cursor: pointer; font-weight: 600; }
        .cg-toggle-merge, .cg-create-composite { border: 0; border-radius: 10px; padding: 8px 12px; background: var(--primary-color); color: #fff; cursor: pointer; font-weight: 600; }
        .cg-room-link { color: var(--primary-color); text-decoration: underline; font-weight: 600; }
        .cg-global-status { font-size: 12px; color: var(--secondary-text-color); }
        .cg-merge-status { font-size: 12px; color: var(--secondary-text-color); }
      </style>
      <div class="cg-shell">
        ${this._renderPanelUpdateBanner()}
        <div class="cg-head">
          <img class="cg-logo" src="${this._logoSrc()}" alt="Concierge">
          <div>
            <div class="cg-title">Concierge</div>
            <div class="cg-subtitle">Global settings and room configuration status</div>
          </div>
        </div>

        ${this._renderBreadcrumb([{ label: "Home Assistant" }, { label: "Concierge" }])}

        <div class="cg-settings-summary">
          <div class="cg-settings-head">
            <div>
              <div class="cg-settings-title">Global Settings</div>
              <div class="cg-settings-copy">Global context sources and integration-level audit wiring.</div>
            </div>
            <ha-button class="cg-settings-gear-btn" data-open-global-settings appearance="plain">&#9881; Edit</ha-button>
          </div>
          <div class="cg-settings-grid">
            <div class="cg-settings-item">
              <div class="cg-settings-item-label">Outside Weather</div>
              <div class="cg-settings-item-value">${this._escapeHtml(weatherSummary)}</div>
            </div>
            <div class="cg-settings-item">
              <div class="cg-settings-item-label">News</div>
              <div class="cg-settings-item-value">${this._escapeHtml(newsSummary)}</div>
            </div>
            <div class="cg-settings-item">
              <div class="cg-settings-item-label">Alarm Status</div>
              <div class="cg-settings-item-value">${this._escapeHtml(alarmSummary)}</div>
            </div>
            <div class="cg-settings-item">
              <div class="cg-settings-item-label">Audit Archive</div>
              <div class="cg-settings-item-value">${this._escapeHtml(`${archiveEnabled ? archiveEnabledMessage : archiveDisabledMessage} (${archiveDestinationUri || "Not configured"})`)}</div>
            </div>
            <div class="cg-settings-item">
              <div class="cg-settings-item-label">AI Source</div>
              <div class="cg-settings-item-value">${this._escapeHtml(aiSummary)}</div>
            </div>
            <div class="cg-settings-item">
              <div class="cg-settings-item-label">TTS Source</div>
              <div class="cg-settings-item-value">${this._escapeHtml(ttsSummary)}</div>
            </div>
            <div class="cg-settings-item">
              <div class="cg-settings-item-label">Asset Exposure</div>
              <div class="cg-settings-item-value">${this._escapeHtml(assetSummary)}</div>
            </div>
            <div class="cg-settings-item">
              <div class="cg-settings-item-label">Voice Enrollment Capability</div>
              <div class="cg-settings-item-value">${this._escapeHtml(voiceEnrollmentSummary)}</div>
            </div>
          </div>
        </div>
        ${globalSettingsDialogMarkup}

        <div class="cg-global" style="margin-bottom: 12px;">
          <div class="cg-global-title">People Setup</div>
          <div class="cg-global-copy">People profiles hold consent, device bindings, and voice attribution state.</div>
          <div class="cg-grid" style="margin-top: 12px;">${peopleMarkup}</div>
        </div>

        <div class="cg-rooms-title">Rooms</div>
        <div class="cg-global cg-merge-controls" style="margin-bottom: 12px;">
          <div class="cg-global-title">Merged Rooms</div>
          <div class="cg-global-copy">Create a merged room from same-floor room cards.</div>
          <div class="cg-row-end" style="margin-top: 10px;">
            <button class="cg-toggle-merge">${this._mergeMode ? "Cancel Merge" : "Merge Rooms"}</button>
            ${this._mergeMode ? `<input id="cg-merge-name" type="text" placeholder="Merged room name" style="min-height:34px; min-width:260px;" value="${this._escapeHtml(this._mergeDraftName)}">` : ""}
            ${this._mergeMode ? '<button class="cg-create-composite">Create Merged Room</button>' : ""}
            <span class="cg-merge-status"></span>
          </div>
        </div>
        ${roomsMarkup}
      </div>
    `;

    this._bindEvents();
    this._renderMergeStatus();
  }

  _renderRoomDetail(areaId) {
    const area = this._areas.find((item) => item.id === areaId);
    if (!area) {
      this._goHome();
      return;
    }

    if (!this._activityTimelineLoaded && !this._activityTimelineLoading) {
      this._loadActivityTimeline(false);
    }

    const room = this._rooms[areaId] || {};
    const floorLabel = String(
      area.floor_name
      || this._floors.find((item) => item.floor_id === area.floor_id)?.name
      || "Unassigned"
    );
    const catalog = this._roomCatalog[areaId] || {};
    this._loadTtsCatalog(false);
    const posture = room.posture || "day";
    const hasAssetIntelligence = Boolean(this._assetIntelligenceConnected);
    const capabilityFlags = this._integrationOptions?.capabilities || {};
    const capPersona = Boolean(capabilityFlags.cap_persona);
    const capAi = Boolean(capabilityFlags.cap_ai);
    const capAssets = Boolean(capabilityFlags.cap_assets);
    const activeActivityFilter = String(this._activityTimelineFilter || "all").toLowerCase();
    const scopedActivityRows = this._filteredActivityTimeline().filter((event) => String(event?.resolved_area_id || "") === String(areaId));
    const selectedActivity = scopedActivityRows.find((event) => String(event?.activity_id || "") === String(this._activityDetailsDialog?.activityId || "")) || null;
    const activityCategory = selectedActivity ? this._activityCategory(selectedActivity) : "";
    const scopedActivityMarkup = scopedActivityRows.length
      ? scopedActivityRows.slice(0, 12).map((event) => {
          const activityId = String(event?.activity_id || "");
          const startedAt = event?.started_at ? new Date(event.started_at).toLocaleString() : "Unknown";
          const channel = event?.channel || "unknown";
          const actor = event?.actor_class || "unknown";
          const intentClass = event?.intent_class || "unknown";
          const requestSummary = event?.request_summary || "";
          const outcome = event?.outcome || "pending";
          return `
            <button type="button" class="cg-selected-source cg-activity-item" data-activity-id="${this._escapeHtml(activityId)}" data-area-id="${this._escapeHtml(areaId)}" style="background: var(--ha-card-background, var(--card-background-color)); border:1px solid var(--divider-color); text-align:left; width:100%; cursor:pointer;">
              <div class="cg-selected-source-label">
                <div><strong>${this._escapeHtml(startedAt)}</strong> - ${this._escapeHtml(channel)} - ${this._escapeHtml(actor)} - ${this._escapeHtml(intentClass)}</div>
                <div class="cg-room-meta">${this._escapeHtml(requestSummary || "No summary")}</div>
              </div>
              <div class="cg-room-meta">${this._escapeHtml(outcome)}</div>
            </button>
          `;
        }).join("")
      : `<div class="cg-selected-empty">${this._activityTimelineLoading ? "Loading activity timeline..." : "No room activity records for this filter/search."}</div>`;

    const diffRef = selectedActivity && Array.isArray(selectedActivity.external_refs)
      ? selectedActivity.external_refs.find((ref) => String(ref?.ref_type || "") === "room_config_diff")
      : null;
    const diffChanges = Array.isArray(diffRef?.changes) ? diffRef.changes : [];
    const diffMarkup = diffChanges.length
      ? diffChanges.map((change) => {
          const fieldLabel = this._humanizeEntityId(String(change?.field || ""));
          const added = Array.isArray(change?.added) ? change.added : [];
          const removed = Array.isArray(change?.removed) ? change.removed : [];
          return `
            <div class="cg-config-card" style="padding:10px; box-shadow:none; border:1px solid var(--divider-color);">
              <div class="cg-config-title" style="font-size:14px;">${this._escapeHtml(fieldLabel)}</div>
              <div class="cg-room-meta"><strong>Added:</strong> ${added.length ? this._escapeHtml(added.map((item) => item.label || item.entity_id).join(", ")) : "None"}</div>
              <div class="cg-room-meta"><strong>Removed:</strong> ${removed.length ? this._escapeHtml(removed.map((item) => item.label || item.entity_id).join(", ")) : "None"}</div>
            </div>
          `;
        }).join("")
      : `<div class="cg-muted">No added/removed details recorded for this activity.</div>`;

    const roomTtsVoice = String(this._roomPersonaDraftValue(areaId, "tts_voice", room.tts_voice || "")).trim();
    const savedRoomTtsLanguage = String(this._roomPersonaDraftValue(areaId, "tts_language", room.tts_language || "")).trim();
    const roomTtsLanguage = this._resolveCatalogLanguageKey(savedRoomTtsLanguage, savedRoomTtsLanguage);
    const catalogDefaultLanguage = this._resolveCatalogLanguageKey(this._ttsCatalog.defaultLanguage, this._ttsCatalog.defaultLanguage || "");

    const languageRows = this._ttsCatalog.languages.length
      ? this._ttsCatalog.languages.slice()
      : [];
    if (roomTtsLanguage && !languageRows.includes(roomTtsLanguage)) {
      languageRows.push(roomTtsLanguage);
    }
    const effectiveLanguage = roomTtsLanguage || catalogDefaultLanguage || languageRows[0] || "";
    const defaultLanguageLabel = effectiveLanguage
      ? (this._ttsCatalog.languageLabels?.[effectiveLanguage] || effectiveLanguage)
      : "";

    const voiceRowsCatalog = Array.isArray(this._ttsCatalog.voicesByLanguage?.[effectiveLanguage])
      ? this._ttsCatalog.voicesByLanguage[effectiveLanguage].map((row) => ({
          entity_id: row.voice_id,
          display_name: row.voice_name,
        }))
      : [];
    const ttsVoiceRows = voiceRowsCatalog.slice();
    if (roomTtsVoice && !ttsVoiceRows.some((row) => row.entity_id === roomTtsVoice)) {
      ttsVoiceRows.push({ entity_id: roomTtsVoice, display_name: roomTtsVoice });
    }
    const ttsLanguageOptions = [
      {
        value: "",
        label: defaultLanguageLabel ? `Default (${defaultLanguageLabel})` : "Default",
      },
      ...languageRows.map((language) => ({
        value: language,
        label: this._ttsCatalog.languageLabels?.[language] || language,
      })),
    ];
    const ttsVoiceOptions = [
      { value: "", label: "Default" },
      ...ttsVoiceRows.map((row) => ({
        value: row.entity_id,
        label: row.display_name,
      })),
    ];

    const roomVoiceDialogOpen = Boolean(this._roomVoiceDialog?.open && this._roomVoiceDialog?.areaId === areaId);
    const aiKnowledgeEnabled = Boolean(room.ai_knowledge_enabled);

    const activitySourceMarkup = "";

    const leftColumnMarkup = `
      <div class="cg-config-card cg-room-device-groups-card">
        <div class="cg-column-head">
          <div>
            <div class="cg-config-title">Room Devices</div>
            <div class="cg-muted">All devices and sensors are managed as grouped lists.</div>
          </div>
          <div class="cg-column-actions" data-room-section-actions data-area-id="${this._escapeHtml(areaId)}" data-room-section="room_devices" style="display:${this._hasRoomSectionDraft(areaId, "room_devices") ? "flex" : "none"};">
            <ha-button class="cg-room-section-cancel" data-area-id="${this._escapeHtml(areaId)}" data-room-section="room_devices">Cancel</ha-button>
            <ha-button class="cg-room-section-save" data-area-id="${this._escapeHtml(areaId)}" data-room-section="room_devices">Save</ha-button>
          </div>
        </div>
        ${this._renderRoomDeviceGroupsEditor(areaId, this._roomDeviceGroups(room), "No room device groups configured yet")}
      </div>
    `;

    const middleColumnMarkup = this._renderInformationSourcesCards({
      scopeId: areaId,
      aiKnowledgeEnabled,
      weatherSourceEntityIds: this._selectedIds(room, "weather_source_entity_ids"),
      newsSourceEntityIds: this._selectedIds(room, "news_source_entity_ids"),
      environmentInformationOutputs: this._selectedIds(room, "environment_information_outputs"),
      assetRows: catalog.asset_device_rows || [],
      assetGroups: this._roomAssetGroups(room),
      assetEmptyLabel: "No asset groups configured yet",
      hasAssetIntelligence,
      canConfigureAi: capAi,
      canUseAssets: capAssets,
    });

    const rightColumnMarkup = `
      <div class="cg-config-card">
        <div class="cg-config-title">Activity</div>
        <div class="cg-muted">A log of activites for the ${this._escapeHtml(area.name || area.id)}</div>
        <div class="cg-muted" style="margin-top: 10px;">Room configuration and interaction events appear below in Room Activity Timeline.</div>
      </div>
      <div class="cg-config-card">
        <div class="cg-config-title">Room Activity Timeline</div>
        <div class="cg-activity-filters" style="margin-top: 10px;">
          ${["all", "voice", "mobile", "automation", "other"].map((filterKey) => `
            <button type="button" class="cg-filter-chip ${activeActivityFilter === filterKey ? "active" : ""}" data-activity-filter="${this._escapeHtml(filterKey)}">${this._escapeHtml(this._activityFilterLabel(filterKey))}</button>
          `).join("")}
        </div>
        <div class="cg-field" style="margin-top: 10px;">
          <label for="cg-activity-search">Search Activity</label>
          <input id="cg-activity-search" type="text" value="${this._escapeHtml(this._activityTimelineSearch || "")}" placeholder="Search by channel, actor, intent, person, room, or summary">
        </div>
        <div class="cg-room-meta" style="margin-top: 6px;">Showing ${this._escapeHtml(String(Math.min(scopedActivityRows.length, 12)))} of ${this._escapeHtml(String(scopedActivityRows.length))} room records.</div>
        <div class="cg-selected-sources" style="margin-top: 10px;">
          ${scopedActivityMarkup}
        </div>
      </div>
    `;

    this.innerHTML = `
      <style>
        .cg-shell { padding: 24px; font-family: var(--primary-font-family); color: var(--primary-text-color); }
        .cg-head { display: flex; align-items: center; gap: 16px; margin-bottom: 18px; }
        .cg-logo { height: 34px; width: 34px; object-fit: contain; }
        .cg-title { font-size: 24px; font-weight: 700; }
        .cg-subtitle { opacity: 0.72; margin-top: 4px; }
        .cg-breadcrumb { font-size: 14px; margin-bottom: 12px; font-weight: 400; color: var(--secondary-text-color); padding: 8px 12px; border-radius: 10px; background: color-mix(in srgb, var(--card-background-color) 88%, var(--primary-color) 12%); }
        .cg-breadcrumb button { appearance: none; border: none; background: transparent; padding: 0; margin: 0; font: inherit; color: var(--secondary-text-color); cursor: pointer; text-decoration: underline; }
        .cg-breadcrumb-current { font-size: 14px; font-weight: 600; color: var(--primary-text-color); }
        .cg-room-top { margin-top: 14px; margin-bottom: 14px; }
        .cg-room-columns { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; align-items: start; }
        .cg-room-column { display: grid; gap: 14px; }
        .cg-config-card { border-radius: 16px; padding: 14px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,0.08)); }
        .cg-column-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
        .cg-column-actions { display: none; align-items: center; gap: 8px; }
        .cg-column-actions ha-button { --mdc-theme-primary: var(--primary-color); }
        .cg-config-title { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
        .cg-config-title-note { font-size: 12px; font-weight: 500; color: var(--secondary-text-color); }
        .cg-field { display: grid; gap: 4px; }
        .cg-field label { font-size: 12px; color: var(--secondary-text-color); }
        .cg-field select, .cg-field input, .cg-field textarea, .cg-field ha-select { min-height: 34px; width: 100%; }
        .cg-row-end { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
        .cg-save-room-persona { border: 0; border-radius: 10px; padding: 8px 12px; background: var(--primary-color); color: #fff; cursor: pointer; font-weight: 600; }
        .cg-room-status { font-size: 12px; color: var(--secondary-text-color); }
        .cg-muted { color: var(--secondary-text-color); font-size: 13px; }
        .cg-selected-sources { display: grid; gap: 6px; margin-top: 8px; }
        .cg-selected-source { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 10px; border-radius: 10px; padding: 8px 0 8px 10px; background: var(--ha-card-background, var(--card-background-color)); border: 1px solid var(--divider-color); }
        .cg-selected-source-label { display: flex; align-items: center; gap: 6px; min-width: 0; }
        .cg-selected-source-text { min-width: 0; }
        .cg-selected-source-primary { font-size: 13px; color: var(--primary-text-color); line-height: 1.3; }
        .cg-selected-source-secondary { font-size: 11px; color: var(--secondary-text-color); line-height: 1.25; margin-top: 1px; }
        .cg-remove-source { justify-self: end; margin: 0; }
        .cg-remove-source { justify-self: end; margin: 0; border-radius: 999px; background: color-mix(in srgb, var(--error-color) 16%, transparent); color: var(--error-color); --mdc-theme-primary: var(--error-color); --mdc-button-horizontal-padding: 10px; }
        .cg-selected-empty { font-size: 12px; color: var(--secondary-text-color); }
        .cg-drag-handle { color: var(--secondary-text-color); font-family: monospace; cursor: grab; user-select: none; }
        .cg-room-selected-item.cg-dragging { opacity: 0.5; }
        .cg-source-picker-row { --cg-source-action-width: 52px; --cg-source-gap: 8px; display: grid; grid-template-columns: minmax(0, 1fr) var(--cg-source-action-width); gap: var(--cg-source-gap); align-items: center; }
        .cg-source-picker-row .cg-room-source-select, .cg-source-picker-row ha-select { width: 100%; min-width: 0; min-height: 42px; border-radius: 8px; border: 1px solid var(--divider-color); padding: 0 10px; background: var(--ha-card-background, var(--card-background-color)); color: var(--primary-text-color); }
        .cg-add-source { --mdc-theme-primary: var(--primary-color); }
        .cg-add-source { width: var(--cg-source-action-width, 52px); justify-self: end; }
        .cg-add-source[disabled] { opacity: 0.55; }
        .cg-source-selection-list { margin-right: calc(var(--cg-source-action-width, 52px) + var(--cg-source-gap, 8px)); }
        .cg-switch-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
        .cg-activity-filters { display: flex; flex-wrap: wrap; gap: 8px; }
        .cg-filter-chip { border: 1px solid var(--divider-color); border-radius: 999px; padding: 6px 12px; background: var(--ha-card-background, var(--card-background-color)); color: var(--primary-text-color); cursor: pointer; font-size: 12px; font-weight: 600; }
        .cg-filter-chip.active { border-color: var(--primary-color); background: color-mix(in srgb, var(--primary-color) 18%, var(--ha-card-background, var(--card-background-color))); color: var(--primary-color); }
        @media (max-width: 1200px) { .cg-room-columns { grid-template-columns: 1fr; } }
      </style>
      <div class="cg-shell">
        ${this._renderPanelUpdateBanner()}
        <div class="cg-head">
          <img class="cg-logo" src="${this._logoSrc()}" alt="Concierge">
          <div>
            <div class="cg-title">${this._escapeHtml(area.name || area.id)}</div>
            <div class="cg-subtitle">Room configuration · Floor: ${this._escapeHtml(floorLabel)}</div>
          </div>
        </div>

        ${this._renderBreadcrumb([
          { label: "Concierge", nav: "home" },
          { label: area.name || area.id, roomId: areaId },
        ])}

        <div class="cg-config-card cg-room-top" style="display:${capPersona ? "block" : "none"};">
          <div class="cg-config-title">Room Persona</div>
          <div class="cg-field">
            <label>Room Posture</label>
            <div class="cg-room-meta">${this._escapeHtml(posture)}</div>
          </div>
          <div class="cg-field" style="margin-top: 10px;">
            <label>Language</label>
            <ha-select
              data-area-id="${this._escapeHtml(areaId)}"
              data-field-key="tts_language"
              data-room-section="persona"
              data-label="Language"
              data-current-value="${this._escapeHtml(roomTtsLanguage)}"
              data-options-json="${this._escapeHtml(JSON.stringify(ttsLanguageOptions))}"
              naturalMenuWidth
              fixedMenuPosition
            ></ha-select>
          </div>
          <div class="cg-field" style="margin-top: 10px;">
            <label>Voice</label>
            <ha-select
              data-area-id="${this._escapeHtml(areaId)}"
              data-field-key="tts_voice"
              data-room-section="persona"
              data-label="Voice"
              data-current-value="${this._escapeHtml(roomTtsVoice)}"
              data-options-json="${this._escapeHtml(JSON.stringify(ttsVoiceOptions))}"
              naturalMenuWidth
              fixedMenuPosition
            ></ha-select>
          </div>
          <div class="cg-field">
            <label>Persona Title</label>
            <input type="text" data-area-id="${this._escapeHtml(areaId)}" data-field-key="persona" data-room-section="persona" value="${this._escapeHtml(this._roomPersonaDraftValue(areaId, "persona", room.persona || ""))}">
          </div>
          <div class="cg-field" style="margin-top: 10px;">
            <label>Persona Paragraph</label>
            <textarea data-area-id="${this._escapeHtml(areaId)}" data-field-key="persona_prompt" data-room-section="persona" rows="5">${this._escapeHtml(this._roomPersonaDraftValue(areaId, "persona_prompt", room.persona_prompt || ""))}</textarea>
          </div>
          <div class="cg-row-end">
            <ha-button class="cg-save-room-persona" data-area-id="${this._escapeHtml(areaId)}" variant="brand">Save</ha-button>
            <ha-button class="cg-listen-room-persona" data-area-id="${this._escapeHtml(areaId)}" appearance="plain">Try Voice</ha-button>
            <span class="cg-room-status" data-area-id="${this._escapeHtml(areaId)}"></span>
          </div>
        </div>

        ${roomVoiceDialogOpen ? "" : ""}

        ${this._activityDetailsDialog?.open && selectedActivity ? `
          <ha-dialog
            open
            scrimClickAction
            escapeKeyAction
            hideActions
            data-activity-detail-dialog
            header-title="Activity Details"
          >
            <div style="padding: 0 16px 16px; display:grid; gap:10px;">
              <div class="cg-modal-copy">${this._escapeHtml(selectedActivity.request_summary || "Room activity")}</div>
              <div class="cg-room-meta"><strong>When:</strong> ${this._escapeHtml(selectedActivity.started_at ? new Date(selectedActivity.started_at).toLocaleString() : "Unknown")}</div>
              <div class="cg-room-meta"><strong>Category:</strong> ${this._escapeHtml(activityCategory)}</div>
              <div class="cg-room-meta"><strong>Completed:</strong> ${this._escapeHtml(selectedActivity.ended_at ? new Date(selectedActivity.ended_at).toLocaleString() : "In progress")}</div>
              <div class="cg-room-meta"><strong>Outcome:</strong> ${this._escapeHtml(selectedActivity.outcome || "pending")}</div>
              ${diffMarkup}
            </div>
            <ha-dialog-footer slot="footer">
              <ha-button slot="primaryAction" variant="brand" data-activity-detail-close>Close</ha-button>
            </ha-dialog-footer>
          </ha-dialog>
        ` : ""}

        <div class="cg-room-columns">
          <div class="cg-room-column">
            ${leftColumnMarkup}
          </div>
          <div class="cg-room-column">
            <div class="cg-config-card">
              <div class="cg-column-head">
                <div>
                  <div class="cg-config-title">Information Sources</div>
                  <div class="cg-muted">Select the Information Sources for the ${this._escapeHtml(area.name || area.id)}</div>
                </div>
                <div class="cg-column-actions" data-room-section-actions data-area-id="${this._escapeHtml(areaId)}" data-room-section="information_sources" style="display:${this._hasRoomSectionDraft(areaId, "information_sources") ? "flex" : "none"};">
                  <ha-button class="cg-room-section-cancel" data-area-id="${this._escapeHtml(areaId)}" data-room-section="information_sources">Cancel</ha-button>
                  <ha-button class="cg-room-section-save" data-area-id="${this._escapeHtml(areaId)}" data-room-section="information_sources">Save</ha-button>
                </div>
              </div>
            </div>
            ${middleColumnMarkup}
          </div>
          <div class="cg-room-column">
            ${rightColumnMarkup}
          </div>
        </div>
      </div>
    `;

    this._bindEvents();
  }

  _renderPersonDetail(personId) {
    const person = this._peopleRegistry[personId];
    if (!person) {
      this._goHome();
      return;
    }

    const profile = this._people[personId] || {};
    const personName = person.name || person.entity_id || personId;
    const selectedVoiceProfileId = typeof profile.voice_profile_id === "string" ? profile.voice_profile_id : "";
    const derivedVoiceProfileId = this._deriveVoiceProfileId(personId);
    const activeVoiceProfileId = selectedVoiceProfileId || (this._voiceProfiles[derivedVoiceProfileId] ? derivedVoiceProfileId : "");
    const enrollmentProfile = activeVoiceProfileId ? this._voiceProfiles[activeVoiceProfileId] : null;
    const enrollmentSamples = Array.isArray(enrollmentProfile?.sample_items) ? enrollmentProfile.sample_items : [];
    const enrollmentState = String(enrollmentProfile?.enrollment_state || "untrained").trim() || "untrained";
    const enrollmentSampleCount = Number(enrollmentProfile?.sample_count || enrollmentSamples.length || 0);
    const enrollmentConfidence = enrollmentProfile?.attribution_confidence;
    const enrollmentConsent = enrollmentProfile?.consent?.voice_enrollment && typeof enrollmentProfile.consent.voice_enrollment === "object"
      ? enrollmentProfile.consent.voice_enrollment
      : {};
    const enrollmentConsentAcknowledged = Boolean(enrollmentConsent.consent_acknowledged);
    const enrollmentLocalOnly = enrollmentConsent.local_only !== false;
    const enrollmentLastBuiltAt = String(enrollmentProfile?.last_built_at || "").trim();
    const enrollmentSamplesMarkup = enrollmentSamples.length
      ? enrollmentSamples.map((sample) => {
          const sampleId = String(sample?.sample_id || "").trim();
          const sampleText = String(sample?.speech_text || "").trim() || "(blank speech item)";
          const capturedAt = String(sample?.captured_at || "").trim();
          const source = String(sample?.source || "").trim() || "guided_phrase";
          const capturedLabel = capturedAt ? new Date(capturedAt).toLocaleString() : "Unknown capture time";
          return `
            <div class="cg-selected-source">
              <div class="cg-selected-source-label">
                <div class="cg-selected-source-text">
                  <div class="cg-selected-source-primary">${this._escapeHtml(sampleText)}</div>
                  <div class="cg-selected-source-secondary">${this._escapeHtml(`${source} · ${capturedLabel}`)}</div>
                </div>
              </div>
              ${sampleId ? `<ha-button class="cg-remove-source cg-person-remove-voice-sample" data-person-id="${this._escapeHtml(personId)}" data-sample-id="${this._escapeHtml(sampleId)}">Remove</ha-button>` : ""}
            </div>
          `;
        }).join("")
      : '<div class="cg-selected-empty">No speech items captured yet.</div>';
    const bleSuggestions = Array.isArray(person.ble_device_suggestions) ? person.ble_device_suggestions : [];
    const bleSuggestionSources = person.ble_device_suggestion_sources || {};

    const voiceOptions = [
      `<option value="">Not set</option>`,
      ...Object.values(this._voiceProfiles || {})
        .slice()
        .sort((left, right) => String(left.name || "").localeCompare(String(right.name || "")))
        .map((voiceProfile) => {
          const selected = voiceProfile.voice_profile_id === selectedVoiceProfileId ? " selected" : "";
          return `<option value="${this._escapeHtml(voiceProfile.voice_profile_id)}"${selected}>${this._escapeHtml(voiceProfile.name || voiceProfile.voice_profile_id)}</option>`;
        }),
    ].join("");

    const bleSuggestionsMarkup = bleSuggestions.length
      ? bleSuggestions.map((bleDeviceId) => {
          const sources = Array.isArray(bleSuggestionSources[bleDeviceId]) ? bleSuggestionSources[bleDeviceId] : [];
          const sourceLabel = sources.length
            ? `From attached tracker${sources.length === 1 ? "" : "s"}: ${sources.join(", ")}`
            : "Derived from attached trackers";
          return `
            <div class="cg-room-meta"><strong>${this._escapeHtml(bleDeviceId)}</strong></div>
            <div class="cg-room-meta">${this._escapeHtml(sourceLabel)}</div>
          `;
        }).join("")
      : `<div class="cg-muted">No BLE suggestions were found from attached device trackers.</div>`;

    const bleValue = Array.isArray(profile.ble_device_ids) && profile.ble_device_ids.length
      ? profile.ble_device_ids.join("\n")
      : bleSuggestions.join("\n");
    const aqaraValue = Array.isArray(profile.aqara_presence_entity_ids) ? profile.aqara_presence_entity_ids.join("\n") : "";
    const interactionTargets = profile?.consent?.interaction_targets && typeof profile.consent.interaction_targets === "object"
      ? profile.consent.interaction_targets
      : {};
    const security = profile?.consent?.security && typeof profile.consent.security === "object"
      ? profile.consent.security
      : {};
    const alarmStepUp = security?.alarm_step_up && typeof security.alarm_step_up === "object"
      ? security.alarm_step_up
      : {};
    const mobileNotifyTargetsValue = Array.isArray(interactionTargets.mobile_notify_targets)
      ? interactionTargets.mobile_notify_targets
      : [];
    const preferredMobileTargetValue = typeof interactionTargets.preferred_mobile_target === "string"
      ? interactionTargets.preferred_mobile_target
      : "";
    const trackerEntityIds = Array.isArray(person.device_trackers)
      ? person.device_trackers.filter(Boolean)
      : [];
    const associatedDeviceOptions = trackerEntityIds.map((entityId) => {
      const friendly = this._friendlyEntityName(entityId);
      return {
        value: entityId,
        label: friendly && friendly !== entityId ? `${friendly} (${entityId})` : entityId,
      };
    });
    const appendIfMissing = (value) => {
      if (!value) return;
      if (associatedDeviceOptions.some((item) => item.value === value)) return;
      associatedDeviceOptions.push({
        value,
        label: `${value} (currently saved, not in associated trackers)`,
      });
    };
    mobileNotifyTargetsValue.forEach((value) => appendIfMissing(value));
    appendIfMissing(preferredMobileTargetValue);

    const mobileTargetOptionsMarkup = associatedDeviceOptions.length
      ? associatedDeviceOptions.map((option) => {
          const selected = mobileNotifyTargetsValue.includes(option.value) ? " selected" : "";
          return `<option value="${this._escapeHtml(option.value)}"${selected}>${this._escapeHtml(option.label)}</option>`;
        }).join("")
      : '<option value="" disabled>No associated device trackers found</option>';

    const preferredTargetOptionsMarkup = [
      `<option value="">Not set</option>`,
      ...associatedDeviceOptions.map((option) => {
        const selected = preferredMobileTargetValue === option.value ? " selected" : "";
        return `<option value="${this._escapeHtml(option.value)}"${selected}>${this._escapeHtml(option.label)}</option>`;
      }),
    ].join("");

    const mobileVoiceEndpointEnabled = Boolean(interactionTargets.mobile_voice_endpoint_enabled);
    const stepUpMode = typeof alarmStepUp.mode === "string" && alarmStepUp.mode
      ? alarmStepUp.mode
      : "app_confirmation";
    const stepUpPushConsentRequired = alarmStepUp.push_consent_required !== false;
    const stepUpPinRequired = Boolean(alarmStepUp.pin_required);
    const stepUpModeOptions = [
      { value: "app_confirmation", label: "App confirmation" },
      { value: "spoken_confirmation", label: "Spoken confirmation" },
      { value: "presence_plus_confirmation", label: "Presence plus confirmation" },
    ].map((item) => {
      const selected = item.value === stepUpMode ? " selected" : "";
      return `<option value="${item.value}"${selected}>${item.label}</option>`;
    }).join("");

    const isMinor = Boolean(profile.is_minor);
    const guardianControlsRequired = profile.guardian_controls_required !== undefined
      ? Boolean(profile.guardian_controls_required)
      : isMinor;
    const minorAllowGeneralQna = Boolean(profile.minor_allow_general_qna);
    const defaultIntentAbilities = ["room_context_info", "household_help"];
    const minorAllowedIntentClasses = Array.isArray(profile.minor_allowed_intent_classes)
      ? profile.minor_allowed_intent_classes.filter(Boolean)
      : defaultIntentAbilities;
    const selectedIntentAbilitySet = new Set(minorAllowedIntentClasses);
    if (minorAllowGeneralQna) selectedIntentAbilitySet.add("general_qna");
    const selectedIntentAbilities = Array.from(selectedIntentAbilitySet);
    const intentAbilityCatalog = this._personIntentAbilityCatalog();
    const intentAbilityLabelMap = Object.fromEntries(intentAbilityCatalog.map((item) => [item.value, item.label]));
    const intentAbilityOptions = [`<option value="">Select an intent ability</option>`]
      .concat(intentAbilityCatalog
        .filter((item) => !selectedIntentAbilitySet.has(item.value))
        .map((item) => `<option value="${this._escapeHtml(item.value)}">${this._escapeHtml(item.label)}</option>`))
      .join("");
    const intentAbilitiesMarkup = selectedIntentAbilities.length
      ? selectedIntentAbilities.map((intentClass) => {
          const label = intentAbilityLabelMap[intentClass] || intentClass;
          return `
            <div class="cg-selected-source cg-person-intent-item" data-person-id="${this._escapeHtml(personId)}" data-intent-class="${this._escapeHtml(intentClass)}">
              <div class="cg-selected-source-label">
                <div class="cg-selected-source-text">
                  <div class="cg-selected-source-primary">${this._escapeHtml(label)}</div>
                  <div class="cg-selected-source-secondary">Intent Ability</div>
                </div>
              </div>
              <ha-button appearance="plain" class="cg-remove-source cg-person-remove-intent" data-person-id="${this._escapeHtml(personId)}" data-intent-class="${this._escapeHtml(intentClass)}">Remove</ha-button>
            </div>
          `;
        }).join("")
      : "";

    const minorContentFilterLevel = typeof profile.minor_content_filter_level === "string" && profile.minor_content_filter_level
      ? profile.minor_content_filter_level
      : "strict";
    const contentFilterOptions = [
      { value: "strict", label: "Strict" },
      { value: "balanced", label: "Balanced" },
      { value: "relaxed", label: "Relaxed" },
    ].map((item) => {
      const selected = item.value === minorContentFilterLevel ? " selected" : "";
      return `<option value="${item.value}"${selected}>${item.label}</option>`;
    }).join("");

    const consentPolicyText = "By saving this profile, you confirm that person-level interaction policy and consent settings are being recorded for operational and safety controls.";
    const consentAcknowledged = Boolean(profile?.consent?.privacy_notice_acknowledged);
    const personActionsVisible = this._activeFormDraftScope === `person:${personId}` && this._activeFormDraftDirty;
    const capabilityFlags = this._integrationOptions?.capabilities || {};
    const capAi = Boolean(capabilityFlags.cap_ai);
    const capTts = Boolean(capabilityFlags.cap_tts);
    const capVoiceEnrollment = Boolean(capabilityFlags.cap_voice_enrollment);
    const voiceEnrollmentDialogOpen = Boolean(this._voiceEnrollmentDialog?.open && this._voiceEnrollmentDialog?.personId === personId);
    const voiceEnrollmentPhrases = this._voiceEnrollmentPhrases();
    const voiceEnrollmentPhraseIndex = voiceEnrollmentDialogOpen
      ? Math.max(0, Math.min(this._voiceEnrollmentDialog.phraseIndex, voiceEnrollmentPhrases.length - 1))
      : 0;
    const voiceEnrollmentPhrase = voiceEnrollmentPhrases[voiceEnrollmentPhraseIndex] || "";
    const voiceEnrollmentNextLabel = voiceEnrollmentPhraseIndex >= voiceEnrollmentPhrases.length - 1 ? "Build Profile" : "Next";
    const voiceEnrollmentNextDisabled = voiceEnrollmentDialogOpen && this._voiceEnrollmentDialog.currentCaptured ? "" : " disabled";
    const showVoiceEnrollmentBegin = !activeVoiceProfileId || enrollmentState !== "trained";
    const voiceEnrollmentBeginLabel = activeVoiceProfileId ? "Resume Voice Enrollment" : "Begin Voice Enrollment";
    const selectedCaptureProvider = voiceEnrollmentDialogOpen
      ? (conciergeNormalizeVoiceEnrollmentProvider(this._voiceEnrollmentDialog.captureProvider) || "browser")
      : "browser";
    const voiceRecordingActive = selectedCaptureProvider === "browser"
      && Boolean(this._voiceEnrollmentRecording?.active && this._voiceEnrollmentRecording.personId === personId);
    const voiceRecordButtonLabel = selectedCaptureProvider === "satellite"
      ? "Capture Phrase"
      : (voiceRecordingActive ? "End Record" : "Begin Record");
    const voiceStorageDestination = String(this._archiveStatus?.destination_uri || "").trim();
    const voiceEnrollmentSatelliteOptions = voiceEnrollmentDialogOpen && Array.isArray(this._voiceEnrollmentDialog.satelliteOptions)
      ? this._voiceEnrollmentDialog.satelliteOptions
      : [];
    const voiceEnrollmentCompletionSummary = voiceEnrollmentDialogOpen
      ? this._voiceEnrollmentCompletionStatus(this._voiceEnrollmentDialog)
      : "";
    const voiceEnrollmentInstructions = selectedCaptureProvider === "satellite"
      ? `Click ${voiceRecordButtonLabel}. Concierge will prompt the selected Voice Assistant Satellite and listen for this phrase. After the phrase is captured, ${voiceEnrollmentNextLabel} becomes available.`
      : `Click ${voiceRecordButtonLabel} to start recording and read the sentence, then click End Record when you are done. After the phrase is captured, ${voiceEnrollmentNextLabel} becomes available.`;
    const voiceEnrollmentAuthorized = voiceEnrollmentDialogOpen
      ? conciergeIsVoiceEnrollmentAuthorized(this._voiceEnrollmentDialog)
      : false;
    const voiceEnrollmentBusy = voiceEnrollmentDialogOpen
      ? Boolean(this._voiceEnrollmentDialog.isBusy)
      : false;
    const voiceEnrollmentBusyLabel = String(this._voiceEnrollmentDialog?.busyLabel || "Working on your request...").trim();
    const voiceProviderAvailability = voiceEnrollmentDialogOpen
      ? conciergeGetVoiceEnrollmentProviderAvailability({
        browserAvailable: this._voiceEnrollmentDialog.browserAvailable,
        satelliteCount: voiceEnrollmentSatelliteOptions.length,
      })
      : { browserSelectable: true, satelliteSelectable: true };
    const voiceCaptureButtonDisabled = (!voiceRecordingActive && this._voiceEnrollmentDialog.currentCaptured)
      || voiceEnrollmentBusy
      || !voiceEnrollmentAuthorized
      || (
        selectedCaptureProvider === "satellite"
        && voiceEnrollmentSatelliteOptions.length > 1
        && !String(this._voiceEnrollmentDialog.satelliteEntityId || "").trim()
      )
      ? " disabled"
      : "";
    const voiceNextButtonDisabled = !voiceEnrollmentAuthorized
      || voiceEnrollmentBusy
      || !this._voiceEnrollmentDialog.currentCaptured
      ? " disabled"
      : "";
    const voiceEnrollmentDialogMarkup = capVoiceEnrollment && voiceEnrollmentDialogOpen ? `
      <ha-dialog
        open
        hideActions
        data-voice-enrollment-dialog
        header-title="Voice Enrollment"
      >
        <div style="padding: 0 16px 16px; display:grid; gap:14px;">
          <div class="cg-voice-context-grid">
            <div class="cg-voice-context-item">
              <div class="cg-muted">Enrollment Person</div>
              <div class="cg-voice-context-value">${this._escapeHtml(personName || personId)}</div>
            </div>
            <div class="cg-voice-context-item">
              <div class="cg-muted">Voice Profile</div>
              <div class="cg-voice-context-value">${this._escapeHtml(this._voiceEnrollmentDialog.voiceProfileId || activeVoiceProfileId || derivedVoiceProfileId)}</div>
            </div>
          </div>
          <div class="cg-switch-field">
            <ha-formfield label="I explicitly consent to voice enrollment for this person">
              <ha-checkbox data-person-id="${this._escapeHtml(personId)}" data-voice-field="consent_acknowledged" ${this._voiceEnrollmentDialog.consentAcknowledged ? "checked" : ""}${voiceEnrollmentBusy ? " disabled" : ""}></ha-checkbox>
            </ha-formfield>
          </div>
          <div class="cg-switch-field">
            <ha-formfield label="Keep voice identity processing local-first (recommended)">
              <ha-checkbox data-person-id="${this._escapeHtml(personId)}" data-voice-field="local_only" ${this._voiceEnrollmentDialog.localOnly !== false ? "checked" : ""}${voiceEnrollmentBusy ? " disabled" : ""}></ha-checkbox>
            </ha-formfield>
          </div>
          <div class="cg-muted">${this._escapeHtml(voiceEnrollmentAuthorized ? "Capture transport and phrase workflow are now available." : "Check both authorization boxes to enable capture method, phrase workflow, and completion controls.")}</div>
          ${voiceEnrollmentBusy ? `<div class="cg-voice-busy-banner" role="status" aria-live="polite"><span class="cg-voice-busy-spinner" aria-hidden="true"></span><span>${this._escapeHtml(voiceEnrollmentBusyLabel)}</span></div>` : ""}
          <div class="cg-voice-workflow-block${voiceEnrollmentAuthorized ? "" : " is-disabled"}${voiceEnrollmentBusy ? " is-busy" : ""}">
            <div class="cg-field">
              <label>Capture Method</label>
              <div class="cg-voice-provider-options">
                <label class="cg-voice-provider-option${selectedCaptureProvider === "browser" ? " is-selected" : ""}${voiceProviderAvailability.browserSelectable ? "" : " is-disabled"}${voiceEnrollmentAuthorized ? "" : " is-locked"}">
                  <input type="radio" name="cg-voice-provider-${this._escapeHtml(personId)}" data-person-id="${this._escapeHtml(personId)}" data-voice-field="capture_provider" value="browser" ${selectedCaptureProvider === "browser" ? "checked" : ""}${voiceProviderAvailability.browserSelectable && voiceEnrollmentAuthorized && !voiceEnrollmentBusy ? "" : " disabled"}>
                  <span class="cg-voice-provider-option-title">Browser Microphone</span>
                  <span class="cg-voice-provider-option-copy">${this._escapeHtml(voiceProviderAvailability.browserSelectable ? "Capture the phrase with this browser session." : (this._voiceEnrollmentDialog.browserStatusSummary || "Browser microphone capture is unavailable in this environment."))}</span>
                </label>
                <label class="cg-voice-provider-option${selectedCaptureProvider === "satellite" ? " is-selected" : ""}${voiceProviderAvailability.satelliteSelectable ? "" : " is-disabled"}${voiceEnrollmentAuthorized ? "" : " is-locked"}">
                  <input type="radio" name="cg-voice-provider-${this._escapeHtml(personId)}" data-person-id="${this._escapeHtml(personId)}" data-voice-field="capture_provider" value="satellite" ${selectedCaptureProvider === "satellite" ? "checked" : ""}${voiceProviderAvailability.satelliteSelectable && voiceEnrollmentAuthorized && !voiceEnrollmentBusy ? "" : " disabled"}>
                  <span class="cg-voice-provider-option-title">Voice Assistant Satellite</span>
                  <span class="cg-voice-provider-option-copy">${this._escapeHtml(voiceProviderAvailability.satelliteSelectable ? "Speak and capture the same phrase through an Assist satellite." : "No Voice Assistant satellites are available in this environment.")}</span>
                  ${selectedCaptureProvider === "satellite" ? `
                    <div class="cg-field cg-voice-provider-nested-field">
                      <label>Voice Assistant Device</label>
                      <select data-person-id="${this._escapeHtml(personId)}" data-voice-field="satellite_entity_id" class="cg-room-source-select"${voiceEnrollmentAuthorized && !voiceEnrollmentBusy ? "" : " disabled"}>
                        <option value="">${voiceEnrollmentSatelliteOptions.length === 1 ? "Satellite selected" : "Select Satellite"}</option>
                        ${voiceEnrollmentSatelliteOptions.map((option) => `<option value="${this._escapeHtml(option.entity_id)}"${option.entity_id === this._voiceEnrollmentDialog.satelliteEntityId ? " selected" : ""}>${this._escapeHtml(option.label)}</option>`).join("")}
                      </select>
                      <div class="cg-muted">${voiceEnrollmentSatelliteOptions.length ? "Choose the Assist satellite that should speak and capture this phrase." : "No Assist satellites are currently available."}</div>
                    </div>
                  ` : ""}
                </label>
              </div>
              ${selectedCaptureProvider === "browser" ? `<div class="cg-muted">${this._escapeHtml(this._voiceEnrollmentDialog.browserStatusSummary || "")}</div>` : ""}
            </div>
            <div class="cg-modal-copy">Phrase ${this._escapeHtml(String(voiceEnrollmentPhraseIndex + 1))} of ${this._escapeHtml(String(voiceEnrollmentPhrases.length))}</div>
            <div class="cg-muted">${this._escapeHtml(voiceEnrollmentInstructions)}</div>
            <div class="cg-voice-phrase-card">${this._escapeHtml(voiceEnrollmentPhrase)}</div>
            <div class="cg-voice-context-grid">
              <div class="cg-voice-context-item">
                <div class="cg-muted">Enrollment Progress</div>
                <div class="cg-voice-context-value">${this._escapeHtml(this._voiceEnrollmentDialog.progressSummary || "Waiting for captured phrases.")}</div>
              </div>
              <div class="cg-voice-context-item">
                <div class="cg-muted">Completion Status</div>
                <div class="cg-voice-context-value">${this._escapeHtml(voiceEnrollmentCompletionSummary)}</div>
              </div>
            </div>
            <div class="cg-muted">Recordings are stored under ${this._escapeHtml(voiceStorageDestination || "the configured attached storage root")} in a dedicated Concierge voice enrollment folder.</div>
            <div class="cg-voice-enrollment-status">${this._escapeHtml(this._voiceEnrollmentDialog.status || "")}</div>
            ${selectedCaptureProvider === "browser" && this._voiceEnrollmentDialog.showProviderFallback ? `
              <div>
                <ha-button class="cg-person-voice-provider-fallback" data-person-id="${this._escapeHtml(personId)}"${voiceEnrollmentAuthorized && !voiceEnrollmentBusy ? "" : " disabled"}>Use Voice Assistant Satellite Instead</ha-button>
              </div>
            ` : ""}
          </div>
        </div>
        <div slot="footer" style="display:flex; justify-content:flex-end; gap:10px; padding: 0 16px 16px;">
          <ha-button appearance="plain" class="cg-person-voice-dialog-close" data-person-id="${this._escapeHtml(personId)}"${voiceEnrollmentBusy ? " disabled" : ""}>Cancel</ha-button>
          <ha-button variant="brand" class="cg-person-record-voice-phrase" data-person-id="${this._escapeHtml(personId)}"${voiceCaptureButtonDisabled}>${this._escapeHtml(voiceRecordButtonLabel)}</ha-button>
          <ha-button variant="brand" class="cg-person-next-voice-phrase" data-person-id="${this._escapeHtml(personId)}"${voiceNextButtonDisabled}>${this._escapeHtml(voiceEnrollmentNextLabel)}</ha-button>
        </div>
      </ha-dialog>
    ` : "";

    this.innerHTML = `
      <style>
        .cg-shell { padding: 24px; font-family: var(--primary-font-family); color: var(--primary-text-color); }
        .cg-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
        .cg-logo { height: 34px; width: 34px; object-fit: contain; }
        .cg-title { font-size: 24px; font-weight: 700; }
        .cg-subtitle { opacity: 0.72; margin-top: 4px; }
        .cg-breadcrumb { font-size: 14px; margin-bottom: 12px; font-weight: 400; color: var(--secondary-text-color); padding: 8px 12px; border-radius: 10px; background: color-mix(in srgb, var(--card-background-color) 88%, var(--primary-color) 12%); }
        .cg-breadcrumb button { appearance: none; border: none; background: transparent; padding: 0; margin: 0; font: inherit; color: var(--secondary-text-color); cursor: pointer; text-decoration: underline; }
        .cg-breadcrumb-current { font-size: 14px; font-weight: 600; color: var(--primary-text-color); }
        .cg-stack { display: grid; gap: 14px; margin-top: 14px; }
        .cg-config-card { border-radius: 16px; padding: 14px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,0.08)); }
        .cg-config-title { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
        .cg-field { display: grid; gap: 4px; }
        .cg-field label { font-size: 12px; color: var(--secondary-text-color); }
        .cg-field select, .cg-field input, .cg-field textarea, .cg-field ha-textfield, .cg-field ha-select { min-height: 34px; width: 100%; }
        .cg-switch-field { margin-top: 10px; }
        .cg-switch-field ha-formfield { width: 100%; }
        .cg-voice-library { margin-top: 14px; display: grid; gap: 12px; }
        .cg-ble-suggestions { margin-top: 14px; display: grid; gap: 8px; }
        .cg-apply-ble-suggestions { border: 0; border-radius: 10px; padding: 8px 12px; background: color-mix(in srgb, var(--primary-color) 14%, transparent); color: var(--primary-color); cursor: pointer; font-weight: 700; }
        .cg-muted { color: var(--secondary-text-color); font-size: 13px; }
        .cg-row-end { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
        .cg-save-person { border: 0; border-radius: 10px; padding: 8px 12px; background: var(--primary-color); color: #fff; cursor: pointer; font-weight: 600; }
        .cg-person-status { font-size: 12px; color: var(--secondary-text-color); }
        .cg-column-actions { display: none; align-items: center; gap: 8px; }
        .cg-column-actions ha-button { --mdc-theme-primary: var(--primary-color); }
        .cg-selected-sources { display: grid; gap: 6px; margin-top: 8px; }
        .cg-selected-source { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 10px; border-radius: 10px; padding: 8px 0 8px 10px; background: var(--ha-card-background, var(--card-background-color)); border: 1px solid var(--divider-color); }
        .cg-selected-source-label { display: flex; align-items: center; gap: 6px; min-width: 0; }
        .cg-selected-source-text { min-width: 0; }
        .cg-selected-source-primary { font-size: 13px; color: var(--primary-text-color); line-height: 1.3; }
        .cg-selected-source-secondary { font-size: 11px; color: var(--secondary-text-color); line-height: 1.25; margin-top: 1px; }
        .cg-remove-source { justify-self: end; margin: 0; border-radius: 999px; background: color-mix(in srgb, var(--error-color) 16%, transparent); color: var(--error-color); --mdc-theme-primary: var(--error-color); --mdc-button-horizontal-padding: 10px; }
        .cg-selected-empty { font-size: 12px; color: var(--secondary-text-color); }
        .cg-source-picker-row { --cg-source-action-width: 52px; --cg-source-gap: 8px; display: grid; grid-template-columns: minmax(0, 1fr) var(--cg-source-action-width); gap: var(--cg-source-gap); align-items: center; }
        .cg-source-picker-row .cg-room-source-select, .cg-source-picker-row ha-select { width: 100%; min-width: 0; min-height: 42px; border-radius: 8px; border: 1px solid var(--divider-color); padding: 0 10px; background: var(--ha-card-background, var(--card-background-color)); color: var(--primary-text-color); }
        .cg-add-source { --mdc-theme-primary: var(--primary-color); width: var(--cg-source-action-width, 52px); justify-self: end; }
        .cg-add-source[disabled] { opacity: 0.55; }
        .cg-source-selection-list { margin-right: calc(var(--cg-source-action-width, 52px) + var(--cg-source-gap, 8px)); }
        .cg-voice-meta { font-size: 12px; color: var(--secondary-text-color); margin-top: 6px; }
        .cg-voice-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
        .cg-voice-actions ha-button { --mdc-theme-primary: var(--primary-color); }
        .cg-voice-context-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
        .cg-voice-context-item { border-radius: 10px; padding: 10px 12px; background: color-mix(in srgb, var(--card-background-color) 90%, var(--primary-color) 10%); }
        .cg-voice-context-value { font-size: 13px; color: var(--primary-text-color); font-weight: 600; margin-top: 4px; word-break: break-word; }
        .cg-voice-provider-options { display: grid; gap: 10px; }
        .cg-voice-provider-option { display: grid; gap: 4px; border: 1px solid var(--divider-color); border-radius: 12px; padding: 10px 12px; background: var(--ha-card-background, var(--card-background-color)); cursor: pointer; }
        .cg-voice-provider-option.is-selected { border-color: var(--primary-color); background: color-mix(in srgb, var(--primary-color) 10%, var(--card-background-color) 90%); }
        .cg-voice-provider-option.is-disabled { opacity: 0.55; cursor: not-allowed; }
        .cg-voice-provider-option.is-locked { opacity: 0.7; }
        .cg-voice-provider-option input { margin: 0; }
        .cg-voice-provider-option-title { font-size: 14px; font-weight: 700; color: var(--primary-text-color); }
        .cg-voice-provider-option-copy { font-size: 12px; color: var(--secondary-text-color); }
        .cg-voice-provider-nested-field { margin-top: 10px; padding-top: 10px; border-top: 1px solid color-mix(in srgb, var(--divider-color) 70%, transparent); }
        .cg-voice-workflow-block { display: grid; gap: 14px; }
        .cg-voice-workflow-block.is-disabled { opacity: 0.55; }
        .cg-voice-workflow-block.is-busy { opacity: 0.7; }
        .cg-voice-busy-banner { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 10px; border: 1px solid color-mix(in srgb, var(--primary-color) 35%, var(--divider-color) 65%); background: color-mix(in srgb, var(--primary-color) 14%, var(--card-background-color) 86%); color: var(--primary-text-color); font-size: 13px; font-weight: 600; }
        .cg-voice-busy-spinner { width: 14px; height: 14px; border-radius: 999px; border: 2px solid color-mix(in srgb, var(--primary-color) 20%, transparent); border-top-color: var(--primary-color); animation: cg-spin 0.9s linear infinite; }
        .cg-voice-enrollment-status { font-size: 12px; color: var(--secondary-text-color); margin-top: 8px; }
        @keyframes cg-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .cg-modal-backdrop { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 24px; background: rgba(0, 0, 0, 0.42); }
        .cg-modal { width: min(640px, 100%); border-radius: 18px; padding: 18px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 16px 48px rgba(0, 0, 0, 0.24)); }
        .cg-modal-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
        .cg-modal-title { font-size: 18px; font-weight: 800; }
        .cg-modal-copy { font-size: 13px; color: var(--secondary-text-color); margin-top: 4px; }
        .cg-modal-close { border: 0; background: transparent; cursor: pointer; color: var(--secondary-text-color); font-size: 24px; line-height: 1; }
        .cg-modal-body { display: grid; gap: 14px; }
        .cg-modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
        .cg-modal-cancel, .cg-modal-update { border: 0; border-radius: 10px; padding: 8px 14px; cursor: pointer; font-weight: 700; }
        .cg-modal-cancel { background: color-mix(in srgb, var(--primary-text-color) 8%, transparent); color: var(--primary-text-color); }
        .cg-modal-update { background: var(--primary-color); color: #fff; }
        .cg-modal-update[disabled] { opacity: 0.45; cursor: not-allowed; }
        .cg-voice-phrase-card { border: 1px solid var(--divider-color); border-radius: 12px; padding: 14px; background: color-mix(in srgb, var(--ha-card-background, var(--card-background-color)) 88%, var(--primary-color) 12%); font-size: 16px; line-height: 1.45; color: var(--primary-text-color); }
      </style>
      <div class="cg-shell">
        ${this._renderPanelUpdateBanner()}
        <div class="cg-head">
          <div style="display:flex; align-items:center; gap:16px;">
            <img class="cg-logo" src="${this._logoSrc()}" alt="Concierge">
            <div>
              <div class="cg-title">${this._escapeHtml(personName)}</div>
              <div class="cg-subtitle">Person configuration</div>
            </div>
          </div>
          <div class="cg-column-actions" data-person-actions data-person-id="${this._escapeHtml(personId)}" style="display:${personActionsVisible ? "flex" : "none"};">
            <ha-button class="cg-cancel-person" data-person-id="${this._escapeHtml(personId)}">Cancel</ha-button>
            <ha-button class="cg-save-person" data-person-id="${this._escapeHtml(personId)}">Save</ha-button>
            <span class="cg-person-status" data-person-id="${this._escapeHtml(personId)}"></span>
          </div>
        </div>

        ${this._renderBreadcrumb([
          { label: "Concierge", nav: "home" },
          { label: personName },
        ])}

        <div class="cg-stack">
          <div class="cg-config-card">
            <div class="cg-config-title">Person Identity</div>
            <div class="cg-field" style="margin-top: 10px;">
              <label>Location</label>
              <ha-area-picker
                data-person-id="${this._escapeHtml(personId)}"
                data-field-key="linked_area_id"
                data-initial-value="${this._escapeHtml(profile.linked_area_id || "")}">
              </ha-area-picker>
            </div>
            <div class="cg-field" style="margin-top: 10px;">
              <label>Voice Profile</label>
              <select data-person-id="${this._escapeHtml(personId)}" data-field-key="voice_profile_id" class="cg-room-source-select" ${capTts ? "" : "disabled"}>
                ${voiceOptions}
              </select>
            </div>
          </div>

          <div class="cg-config-card">
            <div class="cg-config-title">Voice Enrollment</div>
            <div class="cg-muted">Guided local-first enrollment uses a standard set of phrases to build this person's voice profile.</div>
            ${!capVoiceEnrollment ? `<div class="cg-muted">${this._escapeHtml(String(this._integrationOptions?.voice_enrollment_status_summary || "Voice enrollment is unavailable until integration prerequisites are met.").trim())}</div>` : ""}
            <div class="cg-voice-meta">Profile ID: ${this._escapeHtml(activeVoiceProfileId || derivedVoiceProfileId)}</div>
            <div class="cg-voice-meta">State: ${this._escapeHtml(enrollmentState)}</div>
            <div class="cg-voice-meta">Samples: ${this._escapeHtml(String(enrollmentSampleCount))}</div>
            <div class="cg-voice-meta">Confidence: ${this._escapeHtml(enrollmentConfidence === undefined || enrollmentConfidence === null ? "Not built" : Number(enrollmentConfidence).toFixed(2))}</div>
            <div class="cg-voice-meta">Last built: ${this._escapeHtml(enrollmentLastBuiltAt || "Not built yet")}</div>
            <div class="cg-voice-actions">
              ${capVoiceEnrollment && showVoiceEnrollmentBegin ? `<ha-button class="cg-person-begin-enrollment" data-person-id="${this._escapeHtml(personId)}">${this._escapeHtml(voiceEnrollmentBeginLabel)}</ha-button>` : ""}
              ${activeVoiceProfileId ? `<ha-button class="cg-person-delete-voice" data-person-id="${this._escapeHtml(personId)}">Delete</ha-button>` : ""}
            </div>
            <div class="cg-voice-enrollment-status" data-person-id="${this._escapeHtml(personId)}">${this._escapeHtml(activeVoiceProfileId ? "" : (capVoiceEnrollment ? "No voice profile enrolled yet." : String(this._integrationOptions?.voice_enrollment_status_summary || "Voice enrollment is unavailable until integration prerequisites are met.").trim()))}</div>
          </div>

          <div class="cg-config-card">
            <div class="cg-config-title">Minor Interaction Policy</div>
            <div class="cg-muted">Minor classification is explicit and never inferred.</div>
            <div class="cg-switch-field">
              <ha-formfield label="Person is a minor">
                <ha-switch data-person-id="${this._escapeHtml(personId)}" data-field-key="is_minor" ${isMinor ? "checked" : ""}></ha-switch>
              </ha-formfield>
            </div>
            <div class="cg-switch-field">
              <ha-formfield label="Guardian controls required">
                <ha-switch data-person-id="${this._escapeHtml(personId)}" data-field-key="guardian_controls_required" ${guardianControlsRequired ? "checked" : ""}></ha-switch>
              </ha-formfield>
            </div>
          </div>

          <div class="cg-config-card" style="display:${capAi ? "block" : "none"};">
            <div class="cg-config-title">Interactions</div>
            <div class="cg-muted">Configure allowed intent abilities for this person.</div>
            <div class="cg-field" style="margin-top: 10px;">
              <label>Allowed Intent Abilities</label>
              <div class="cg-source-picker-row">
                <select data-person-id="${this._escapeHtml(personId)}" data-field-key="minor_intent_ability_picker" class="cg-room-source-select">
                  ${intentAbilityOptions}
                </select>
                <ha-button class="cg-add-source cg-person-add-intent" data-person-id="${this._escapeHtml(personId)}">Add</ha-button>
              </div>
              <div class="cg-selected-sources cg-source-selection-list cg-person-intent-list" data-person-id="${this._escapeHtml(personId)}" data-field-key="minor_intent_ability_list">
                <div class="cg-selected-empty"${intentAbilitiesMarkup ? ' style="display:none;"' : ""}>No sources selected</div>
                ${intentAbilitiesMarkup}
              </div>
              <textarea hidden data-person-id="${this._escapeHtml(personId)}" data-field-key="minor_allowed_intent_classes" rows="1">${this._escapeHtml(selectedIntentAbilities.join("\n"))}</textarea>
            </div>
            <div class="cg-field" style="margin-top: 10px;">
              <label>Content Filter Level</label>
              <select data-person-id="${this._escapeHtml(personId)}" data-field-key="minor_content_filter_level" class="cg-room-source-select">
                ${contentFilterOptions}
              </select>
            </div>
          </div>

          <div class="cg-config-card">
            <div class="cg-ble-suggestions">
              <div class="cg-config-title">Suggested BLE Device IDs</div>
              <div class="cg-muted">Derived from attached device trackers when their device registry entry exposes Bluetooth or MAC connections.</div>
              <div style="display: grid; gap: 6px;">
                ${bleSuggestionsMarkup}
              </div>
              <div class="cg-row-end" style="margin-top: 4px;">
                <button type="button" class="cg-apply-ble-suggestions" data-person-id="${this._escapeHtml(personId)}">Use Suggested BLE Devices</button>
              </div>
            </div>
            <div class="cg-field" style="margin-top: 10px;">
              <label>BLE Device IDs</label>
              <textarea data-person-id="${this._escapeHtml(personId)}" data-field-key="ble_device_ids" rows="4">${this._escapeHtml(bleValue)}</textarea>
            </div>
            <div class="cg-field" style="margin-top: 10px;">
              <label>Aqara Presence Entity IDs</label>
              <textarea data-person-id="${this._escapeHtml(personId)}" data-field-key="aqara_presence_entity_ids" rows="4">${this._escapeHtml(aqaraValue)}</textarea>
            </div>
          </div>

          <div class="cg-config-card">
            <div class="cg-config-title">Mobile Interaction Devices</div>
            <div class="cg-muted">Choose from this person's associated device trackers for mobility and read-later delivery targets.</div>
            <div class="cg-field" style="margin-top: 10px;">
              <label>Mobility Targets</label>
              <select multiple data-person-id="${this._escapeHtml(personId)}" data-field-key="mobile_notify_targets">
                ${mobileTargetOptionsMarkup}
              </select>
            </div>
            <div class="cg-field" style="margin-top: 10px;">
              <label>Preferred Read-Later Target</label>
              <select data-person-id="${this._escapeHtml(personId)}" data-field-key="preferred_mobile_target" class="cg-room-source-select">
                ${preferredTargetOptionsMarkup}
              </select>
            </div>
            <div class="cg-switch-field">
              <ha-formfield label="Enable this person's local voice endpoint on mobile device">
                <ha-switch data-person-id="${this._escapeHtml(personId)}" data-field-key="mobile_voice_endpoint_enabled" ${mobileVoiceEndpointEnabled ? "checked" : ""}></ha-switch>
              </ha-formfield>
            </div>
          </div>

          <div class="cg-config-card">
            <div class="cg-config-title">Alarm Step-Up Consent Delivery</div>
            <div class="cg-muted">When enabled, Concierge pushes step-up consent to this person's device before protected alarm actions.</div>
            <div class="cg-field" style="margin-top: 10px;">
              <label>Step-Up Mode</label>
              <select data-person-id="${this._escapeHtml(personId)}" data-field-key="step_up_mode" class="cg-room-source-select">
                ${stepUpModeOptions}
              </select>
            </div>
            <div class="cg-switch-field">
              <ha-formfield label="Require push consent to the person's device for step-up">
                <ha-switch data-person-id="${this._escapeHtml(personId)}" data-field-key="step_up_push_consent_required" ${stepUpPushConsentRequired ? "checked" : ""}></ha-switch>
              </ha-formfield>
            </div>
            <div class="cg-switch-field">
              <ha-formfield label="Require PIN/unlock on device before approval">
                <ha-switch data-person-id="${this._escapeHtml(personId)}" data-field-key="step_up_pin_required" ${stepUpPinRequired ? "checked" : ""}></ha-switch>
              </ha-formfield>
            </div>
          </div>

          <div class="cg-config-card">
            <div class="cg-config-title">Consent</div>
            <div class="cg-muted">${this._escapeHtml(consentPolicyText)}</div>
            <div class="cg-switch-field">
              <ha-formfield label="I agree to save this person's interaction and consent policy settings">
                <ha-checkbox data-person-id="${this._escapeHtml(personId)}" data-field-key="consent_acknowledged" ${consentAcknowledged ? "checked" : ""}></ha-checkbox>
              </ha-formfield>
            </div>
          </div>

          <div class="cg-config-card">
            <div class="cg-field" style="margin-top: 10px;">
              <label>Notes</label>
              <textarea data-person-id="${this._escapeHtml(personId)}" data-field-key="notes" rows="3">${this._escapeHtml(profile.notes || "")}</textarea>
            </div>
          </div>
        </div>

        ${voiceEnrollmentDialogMarkup}

      </div>
    `;

    this._bindEvents();
  }

  _renderCompositeDetail(compositeId) {
    const composite = this._composites[compositeId];
    if (!composite) {
      this._goHome();
      return;
    }

    const areaIds = Array.isArray(composite.area_ids) ? composite.area_ids : [];
    this._loadTtsCatalog(false);
    const memberNames = this._memberAreaNames(areaIds);
    const firstArea = this._areas.find((item) => item.id === areaIds[0]);
    const floorId = composite.floor_id || firstArea?.floor_id || null;
    const floorLabel = this._floors.find((item) => item.floor_id === floorId)?.name || "Unassigned";

    const catalog = this._compositeCatalog[compositeId] || {};
    const hasAssetIntelligence = Boolean(this._assetIntelligenceConnected);
    const capabilityFlags = this._integrationOptions?.capabilities || {};
    const capPersona = Boolean(capabilityFlags.cap_persona);
    const capAi = Boolean(capabilityFlags.cap_ai);
    const capAssets = Boolean(capabilityFlags.cap_assets);
    const persistedDeviceGroups = this._roomDeviceGroups(composite);
    const combinedDeviceGroups = persistedDeviceGroups.length
      ? persistedDeviceGroups
      : this._combinedDeviceGroupsForAreaIds(areaIds);
    const persistedAssetGroups = this._roomAssetGroups(composite);
    const combinedAssetGroups = persistedAssetGroups.length
      ? persistedAssetGroups
      : this._combinedAssetGroupsForAreaIds(areaIds);
    const combinedWeatherSources = this._combinedFieldEntityIdsForAreaIds(areaIds, "weather_source_entity_ids");
    const combinedNewsSources = this._combinedFieldEntityIdsForAreaIds(areaIds, "news_source_entity_ids");
    const combinedEnvironmentOutputs = this._combinedFieldEntityIdsForAreaIds(areaIds, "environment_information_outputs");
    const roomsForComposite = this._roomsForAreaIds(areaIds);
    const compositeHasAiKnowledge = Object.prototype.hasOwnProperty.call(composite || {}, "ai_knowledge_enabled");
    const aiKnowledgeEnabled = compositeHasAiKnowledge
      ? Boolean(composite.ai_knowledge_enabled)
      : roomsForComposite.some((room) => Boolean(room?.ai_knowledge_enabled));
    const compositeHasWeatherSources = Object.prototype.hasOwnProperty.call(composite || {}, "weather_source_entity_ids");
    const selectedWeatherSources = compositeHasWeatherSources
      ? this._selectedIds(composite, "weather_source_entity_ids")
      : combinedWeatherSources;
    const compositeHasNewsSources = Object.prototype.hasOwnProperty.call(composite || {}, "news_source_entity_ids");
    const selectedNewsSources = compositeHasNewsSources
      ? this._selectedIds(composite, "news_source_entity_ids")
      : combinedNewsSources;
    const compositeHasEnvironmentOutputs = Object.prototype.hasOwnProperty.call(composite || {}, "environment_information_outputs");
    const selectedEnvironmentOutputs = compositeHasEnvironmentOutputs
      ? this._selectedIds(composite, "environment_information_outputs")
      : combinedEnvironmentOutputs;
    const mergedAssetDeviceRows = (() => {
      const byDeviceId = new Map();
      areaIds.forEach((areaId) => {
        this._roomAssetCandidates(areaId).forEach((row) => {
          const deviceId = String(row?.device_id || "").trim();
          if (!deviceId) return;
          const previous = byDeviceId.get(deviceId) || {};
          const labelIds = Array.from(
            new Set([
              ...this._labelIdsFromValue(previous.label_ids || []),
              ...this._labelIdsFromValue(row?.label_ids || []),
            ])
          );
          byDeviceId.set(deviceId, {
            ...row,
            ...previous,
            device_id: deviceId,
            label_ids: labelIds,
          });
        });
      });
      if (byDeviceId.size) return Array.from(byDeviceId.values());
      return Array.isArray(catalog.asset_device_rows) ? catalog.asset_device_rows : [];
    })();
    const compositePosture = composite.posture || "day";

    const compositeTtsVoice = String(this._roomPersonaDraftValue(compositeId, "tts_voice", composite.tts_voice || "")).trim();
    const savedCompositeTtsLanguage = String(this._roomPersonaDraftValue(compositeId, "tts_language", composite.tts_language || "")).trim();
    const compositeTtsLanguage = this._resolveCatalogLanguageKey(savedCompositeTtsLanguage, savedCompositeTtsLanguage);
    const catalogDefaultLanguage = this._resolveCatalogLanguageKey(this._ttsCatalog.defaultLanguage, this._ttsCatalog.defaultLanguage || "");

    const languageRows = this._ttsCatalog.languages.length
      ? this._ttsCatalog.languages.slice()
      : [];
    if (compositeTtsLanguage && !languageRows.includes(compositeTtsLanguage)) {
      languageRows.push(compositeTtsLanguage);
    }
    const effectiveLanguage = compositeTtsLanguage || catalogDefaultLanguage || languageRows[0] || "";
    const defaultLanguageLabel = effectiveLanguage
      ? (this._ttsCatalog.languageLabels?.[effectiveLanguage] || effectiveLanguage)
      : "";

    const voiceRowsCatalog = Array.isArray(this._ttsCatalog.voicesByLanguage?.[effectiveLanguage])
      ? this._ttsCatalog.voicesByLanguage[effectiveLanguage].map((row) => ({
          entity_id: row.voice_id,
          display_name: row.voice_name,
        }))
      : [];
    const ttsVoiceRows = voiceRowsCatalog.slice();
    if (compositeTtsVoice && !ttsVoiceRows.some((row) => row.entity_id === compositeTtsVoice)) {
      ttsVoiceRows.push({ entity_id: compositeTtsVoice, display_name: compositeTtsVoice });
    }
    const ttsLanguageOptions = [
      {
        value: "",
        label: defaultLanguageLabel ? `Default (${defaultLanguageLabel})` : "Default",
      },
      ...languageRows.map((language) => ({
        value: language,
        label: this._ttsCatalog.languageLabels?.[language] || language,
      })),
    ];
    const ttsVoiceOptions = [
      { value: "", label: "Default" },
      ...ttsVoiceRows.map((row) => ({
        value: row.entity_id,
        label: row.display_name,
      })),
    ];

    const compositePersonaCardMarkup = `
      <div class="cg-config-card cg-room-top" style="display:${capPersona ? "block" : "none"};">
        <div class="cg-config-title">Room Persona</div>
        <div class="cg-field">
          <label>Room Posture</label>
          <div class="cg-room-meta">${this._escapeHtml(compositePosture)}</div>
        </div>
        <div class="cg-field" style="margin-top: 10px;">
          <label>Language</label>
          <ha-select
            data-area-id="${this._escapeHtml(compositeId)}"
            data-field-key="tts_language"
            data-room-section="persona"
            data-label="Language"
            data-current-value="${this._escapeHtml(compositeTtsLanguage)}"
            data-options-json="${this._escapeHtml(JSON.stringify(ttsLanguageOptions))}"
            naturalMenuWidth
            fixedMenuPosition
          ></ha-select>
        </div>
        <div class="cg-field" style="margin-top: 10px;">
          <label>Voice</label>
          <ha-select
            data-area-id="${this._escapeHtml(compositeId)}"
            data-field-key="tts_voice"
            data-room-section="persona"
            data-label="Voice"
            data-current-value="${this._escapeHtml(compositeTtsVoice)}"
            data-options-json="${this._escapeHtml(JSON.stringify(ttsVoiceOptions))}"
            naturalMenuWidth
            fixedMenuPosition
          ></ha-select>
        </div>
        <div class="cg-field">
          <label>Persona Title</label>
          <input type="text" data-area-id="${this._escapeHtml(compositeId)}" data-field-key="persona" data-room-section="persona" value="${this._escapeHtml(this._roomPersonaDraftValue(compositeId, "persona", composite.persona || ""))}">
        </div>
        <div class="cg-field" style="margin-top: 10px;">
          <label>Persona Paragraph</label>
          <textarea data-area-id="${this._escapeHtml(compositeId)}" data-field-key="persona_prompt" data-room-section="persona" rows="5">${this._escapeHtml(this._roomPersonaDraftValue(compositeId, "persona_prompt", composite.persona_prompt || ""))}</textarea>
        </div>
        <div class="cg-row-end">
          <ha-button class="cg-save-composite-persona" data-composite-id="${this._escapeHtml(compositeId)}" variant="brand">Save</ha-button>
          <ha-button class="cg-listen-room-persona" data-area-id="${this._escapeHtml(compositeId)}" appearance="plain">Try Voice</ha-button>
          <span class="cg-composite-persona-status" data-composite-id="${this._escapeHtml(compositeId)}"></span>
          <span class="cg-room-status" data-area-id="${this._escapeHtml(compositeId)}"></span>
        </div>
      </div>
    `;

    const leftColumnMarkup = `
      <div class="cg-config-card">
        <div class="cg-column-head">
          <div>
            <div class="cg-config-title">Room Devices</div>
            <div class="cg-muted">All devices and sensors are managed as grouped lists.</div>
          </div>
          <div class="cg-column-actions" data-room-section-actions data-composite-id="${this._escapeHtml(compositeId)}" data-room-section="room_devices" style="display:${this._hasRoomSectionDraft(compositeId, "room_devices") ? "flex" : "none"};">
            <ha-button class="cg-composite-section-cancel" data-composite-id="${this._escapeHtml(compositeId)}" data-room-section="room_devices">Cancel</ha-button>
            <ha-button class="cg-composite-section-save" data-composite-id="${this._escapeHtml(compositeId)}" data-room-section="room_devices">Save</ha-button>
          </div>
        </div>
        ${this._renderRoomDeviceGroupsEditor(compositeId, combinedDeviceGroups, "No combined room device groups found")}
      </div>
    `;

    const middleColumnMarkup = this._renderInformationSourcesCards({
      scopeId: compositeId,
      aiKnowledgeEnabled,
      weatherSourceEntityIds: selectedWeatherSources,
      newsSourceEntityIds: selectedNewsSources,
      environmentInformationOutputs: selectedEnvironmentOutputs,
      assetRows: mergedAssetDeviceRows,
      assetGroups: combinedAssetGroups,
      assetEmptyLabel: "No combined asset groups found",
      hasAssetIntelligence,
      canConfigureAi: capAi,
      canUseAssets: capAssets,
    });

    const rightColumnMarkup = `
      <div class="cg-config-card">
        <div class="cg-config-title">Activity</div>
        <div class="cg-muted">Merged room members on ${this._escapeHtml(floorLabel)} floor.</div>
        <div class="cg-selected-sources" style="margin-top: 10px;">
          ${memberNames.length
    ? memberNames.map((name) => `<div class="cg-selected-source"><div class="cg-selected-source-label">${this._escapeHtml(name)}</div></div>`).join("")
    : '<div class="cg-selected-empty">No rooms currently assigned.</div>'}
        </div>
      </div>
    `;

    this.innerHTML = `
      <style>
        .cg-shell { padding: 24px; font-family: var(--primary-font-family); color: var(--primary-text-color); }
        .cg-head { display: flex; align-items: center; gap: 16px; margin-bottom: 18px; }
        .cg-logo { height: 34px; width: 34px; object-fit: contain; }
        .cg-title { font-size: 24px; font-weight: 700; }
        .cg-subtitle { opacity: 0.72; margin-top: 4px; }
        .cg-breadcrumb { font-size: 14px; margin-bottom: 12px; font-weight: 400; color: var(--secondary-text-color); padding: 8px 12px; border-radius: 10px; background: color-mix(in srgb, var(--card-background-color) 88%, var(--primary-color) 12%); }
        .cg-breadcrumb button { appearance: none; border: none; background: transparent; padding: 0; margin: 0; font: inherit; color: var(--secondary-text-color); cursor: pointer; text-decoration: underline; }
        .cg-breadcrumb-current { font-size: 14px; font-weight: 600; color: var(--primary-text-color); }
        .cg-room-top { margin-top: 14px; margin-bottom: 14px; }
        .cg-room-columns { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; align-items: start; }
        .cg-room-column { display: grid; gap: 14px; }
        .cg-config-card { border-radius: 16px; padding: 14px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,0.08)); }
        .cg-column-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
        .cg-column-actions { display: none; align-items: center; gap: 8px; }
        .cg-column-actions ha-button { --mdc-theme-primary: var(--primary-color); }
        .cg-config-title { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
        .cg-config-title-note { font-size: 12px; font-weight: 500; color: var(--secondary-text-color); }
        .cg-field { display: grid; gap: 4px; }
        .cg-field label { font-size: 12px; color: var(--secondary-text-color); }
        .cg-field select, .cg-field input, .cg-field textarea { min-height: 34px; width: 100%; }
        .cg-multi { min-height: 96px !important; }
        .cg-row-end { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
        .cg-save-composite { border: 0; border-radius: 10px; padding: 8px 12px; background: var(--primary-color); color: #fff; cursor: pointer; font-weight: 600; }
        .cg-composite-status { font-size: 12px; color: var(--secondary-text-color); }
        .cg-muted { color: var(--secondary-text-color); font-size: 13px; }
        .cg-selected-sources { display: grid; gap: 6px; margin-top: 8px; }
        .cg-selected-source { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 10px; border-radius: 10px; padding: 8px 0 8px 10px; background: var(--ha-card-background, var(--card-background-color)); border: 1px solid var(--divider-color); }
        .cg-selected-source-label { display: flex; align-items: center; gap: 6px; min-width: 0; }
        .cg-selected-source-text { min-width: 0; }
        .cg-selected-source-primary { font-size: 13px; color: var(--primary-text-color); line-height: 1.3; }
        .cg-selected-source-secondary { font-size: 11px; color: var(--secondary-text-color); line-height: 1.25; margin-top: 1px; }
        .cg-remove-source { justify-self: end; margin: 0; }
        .cg-remove-source { justify-self: end; margin: 0; border-radius: 999px; background: color-mix(in srgb, var(--error-color) 16%, transparent); color: var(--error-color); --mdc-theme-primary: var(--error-color); --mdc-button-horizontal-padding: 10px; }
        .cg-selected-empty { font-size: 12px; color: var(--secondary-text-color); }
        .cg-source-picker-row { --cg-source-action-width: 52px; --cg-source-gap: 8px; display: grid; grid-template-columns: minmax(0, 1fr) var(--cg-source-action-width); gap: var(--cg-source-gap); align-items: center; }
        .cg-source-picker-row .cg-room-source-select, .cg-source-picker-row ha-select { width: 100%; min-width: 0; min-height: 42px; border-radius: 8px; border: 1px solid var(--divider-color); padding: 0 10px; background: var(--ha-card-background, var(--card-background-color)); color: var(--primary-text-color); }
        .cg-add-source { --mdc-theme-primary: var(--primary-color); width: var(--cg-source-action-width, 52px); justify-self: end; }
        .cg-add-source[disabled] { opacity: 0.55; }
        .cg-source-selection-list { margin-right: calc(var(--cg-source-action-width, 52px) + var(--cg-source-gap, 8px)); }
        @media (max-width: 1200px) { .cg-room-columns { grid-template-columns: 1fr; } }
      </style>
      <div class="cg-shell">
        <div class="cg-head">
          <img class="cg-logo" src="${this._logoSrc()}" alt="Concierge">
          <div>
            <div class="cg-title">${this._escapeHtml(composite.name || compositeId)}</div>
            <div class="cg-subtitle">Merged room configuration</div>
          </div>
        </div>

        ${this._renderBreadcrumb([
          { label: "Concierge", nav: "home" },
          { label: composite.name || compositeId },
        ])}

        ${compositePersonaCardMarkup}

        <div class="cg-room-columns">
          <div class="cg-room-column">
            ${leftColumnMarkup}
          </div>
          <div class="cg-room-column">
            <div class="cg-config-card">
              <div class="cg-column-head">
                <div>
                  <div class="cg-config-title">Information Sources</div>
                  <div class="cg-muted">Select informational sources from all merged rooms.</div>
                </div>
                <div class="cg-column-actions" data-room-section-actions data-composite-id="${this._escapeHtml(compositeId)}" data-room-section="information_sources" style="display:${this._hasRoomSectionDraft(compositeId, "information_sources") ? "flex" : "none"};">
                  <ha-button class="cg-composite-section-cancel" data-composite-id="${this._escapeHtml(compositeId)}" data-room-section="information_sources">Cancel</ha-button>
                  <ha-button class="cg-composite-section-save" data-composite-id="${this._escapeHtml(compositeId)}" data-room-section="information_sources">Save</ha-button>
                </div>
              </div>
            </div>
            ${middleColumnMarkup}
          </div>
          <div class="cg-room-column">
            ${rightColumnMarkup}
          </div>
        </div>
      </div>
    `;

    this._bindEvents();
  }

  _renderError() {
    const hint = String(this._loadError || "").includes("401")
      ? "Your Home Assistant auth token appears unavailable or expired for this panel session. Reload and try again."
      : "";
    this.innerHTML = `
      <div style="padding:24px; color: var(--error-color); font-family: var(--primary-font-family);">
        Failed to load Concierge UI: ${this._escapeHtml(this._loadError || "Unknown error")}
        ${hint ? `<div style="margin-top:8px; color: var(--secondary-text-color);">${this._escapeHtml(hint)}</div>` : ""}
      </div>
    `;
  }

  _render() {
    if (!this._loaded) {
      this._renderStartupLoading();
      return;
    }
    if (this._loadError) {
      this._renderError();
      return;
    }
    if (this._selectedAreaId) {
      this._renderRoomDetail(this._selectedAreaId);
      return;
    }
    if (this._selectedCompositeId) {
      this._renderCompositeDetail(this._selectedCompositeId);
      return;
    }
    if (this._selectedPersonId) {
      this._renderPersonDetail(this._selectedPersonId);
      return;
    }
    this._renderMain();
  }
};

if (!customElements.get("concierge-app")) {
  customElements.define("concierge-app", ConciergeApp);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    conciergeBuildSatelliteEnrollmentPrompt,
    ConciergeApp,
    conciergeBuildVoiceEnrollmentDialogState,
    conciergeCollectSatelliteOptions,
    conciergeGetBrowserVoiceEnrollmentCapability,
    conciergeGetVoiceEnrollmentProviderAvailability,
    conciergeIsVoiceEnrollmentAuthorized,
    conciergeNormalizeVoiceEnrollmentProvider,
    conciergeResolveVoiceEnrollmentDefaultProvider,
  };
}
