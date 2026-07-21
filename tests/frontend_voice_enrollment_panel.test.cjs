const test = require("node:test");
const assert = require("node:assert/strict");

globalThis.HTMLElement = globalThis.HTMLElement || class {};
globalThis.customElements = globalThis.customElements || {
  get() {
    return undefined;
  },
  define() {
    // no-op for tests
  },
};
globalThis.document = globalThis.document || {
  currentScript: null,
  scripts: [],
  visibilityState: "visible",
  addEventListener() {
    // no-op
  },
  removeEventListener() {
    // no-op
  },
};
globalThis.window = globalThis.window || {
  location: { origin: "http://localhost" },
  isSecureContext: true,
  requestAnimationFrame(callback) {
    if (typeof callback === "function") callback();
  },
  addEventListener() {
    // no-op
  },
  removeEventListener() {
    // no-op
  },
};
globalThis.navigator = globalThis.navigator || {
  mediaDevices: {
    getUserMedia() {
      return Promise.resolve({ getTracks() { return []; } });
    },
  },
};
globalThis.MediaRecorder = globalThis.MediaRecorder || class MediaRecorder {
  static isTypeSupported() {
    return true;
  }
};
globalThis.CSS = globalThis.CSS || {
  escape(value) {
    return String(value);
  },
};

const {
  ConciergeApp,
  conciergeBuildSatelliteEnrollmentPrompt,
  conciergeBuildVoiceEnrollmentDialogState,
  conciergeCollectSatelliteOptions,
  conciergeGetBrowserVoiceEnrollmentCapability,
  conciergeGetVoiceEnrollmentProviderAvailability,
  conciergeIsVoiceEnrollmentAuthorized,
  conciergeResolveVoiceEnrollmentDefaultProvider,
} = require("../custom_components/concierge/frontend/panel.js");

test("browser-capable environments default voice enrollment to browser", () => {
  const capability = conciergeGetBrowserVoiceEnrollmentCapability({
    isSecureContext: true,
    mediaDevices: { getUserMedia() {} },
    MediaRecorderCtor: class {},
  });

  const provider = conciergeResolveVoiceEnrollmentDefaultProvider({
    browserAvailable: capability.available,
    satelliteCount: 3,
  });

  assert.equal(provider, "browser");
});

test("browser-ineligible environments default voice enrollment to satellite", () => {
  const capability = conciergeGetBrowserVoiceEnrollmentCapability({
    isSecureContext: false,
    mediaDevices: { getUserMedia() {} },
    MediaRecorderCtor: class {},
  });

  const provider = conciergeResolveVoiceEnrollmentDefaultProvider({
    browserAvailable: capability.available,
    satelliteCount: 2,
  });

  assert.equal(provider, "satellite");
});

test("provider availability disables browser when the environment is not browser-capable", () => {
  const availability = conciergeGetVoiceEnrollmentProviderAvailability({
    browserAvailable: false,
    satelliteCount: 2,
  });

  assert.equal(availability.browserSelectable, false);
  assert.equal(availability.satelliteSelectable, true);
});

test("provider availability disables satellite when no satellites exist", () => {
  const availability = conciergeGetVoiceEnrollmentProviderAvailability({
    browserAvailable: true,
    satelliteCount: 0,
  });

  assert.equal(availability.browserSelectable, true);
  assert.equal(availability.satelliteSelectable, false);
});

test("voice enrollment authorization requires both checkboxes", () => {
  assert.equal(conciergeIsVoiceEnrollmentAuthorized({ consentAcknowledged: false, localOnly: true }), false);
  assert.equal(conciergeIsVoiceEnrollmentAuthorized({ consentAcknowledged: true, localOnly: false }), false);
  assert.equal(conciergeIsVoiceEnrollmentAuthorized({ consentAcknowledged: true, localOnly: true }), true);
});

test("satellite prompt asks for the numbered phrase before capture", () => {
  const prompt = conciergeBuildSatelliteEnrollmentPrompt(
    0,
    "Hello Concierge, please turn on the kitchen lights and set them to seventy percent."
  );

  assert.equal(
    prompt,
    "Please read phrase 1 now."
  );
});

test("satellite options use friendly labels from hass states", () => {
  const options = conciergeCollectSatelliteOptions({
    "assist_satellite.office": {
      attributes: { friendly_name: "Office Voice Assistant" },
    },
    "assist_satellite.kitchen": {
      attributes: { friendly_name: "Kitchen Voice Assistant" },
    },
  });

  assert.deepEqual(options, [
    { entity_id: "assist_satellite.kitchen", label: "Kitchen Voice Assistant" },
    { entity_id: "assist_satellite.office", label: "Office Voice Assistant" },
  ]);
});

test("single satellite is preselected but multiple satellites require explicit selection", () => {
  const singleSatelliteState = conciergeBuildVoiceEnrollmentDialogState({}, {
    open: true,
    personId: "person.tom",
    captureProvider: "satellite",
    satelliteOptions: [{ entity_id: "assist_satellite.office", label: "Office Voice Assistant" }],
    browserAvailable: false,
  });
  const multipleSatelliteState = conciergeBuildVoiceEnrollmentDialogState({}, {
    open: true,
    personId: "person.tom",
    captureProvider: "satellite",
    satelliteOptions: [
      { entity_id: "assist_satellite.office", label: "Office Voice Assistant" },
      { entity_id: "assist_satellite.kitchen", label: "Kitchen Voice Assistant" },
    ],
    browserAvailable: false,
  });

  assert.equal(singleSatelliteState.satelliteEntityId, "assist_satellite.office");
  assert.equal(multipleSatelliteState.satelliteEntityId, "");
});

test("dialog state merge preserves enrollment choices and progress across refreshes", () => {
  const readiness = { ready: false, user_safe_status_summary: "Need one more sample" };
  const previous = conciergeBuildVoiceEnrollmentDialogState({}, {
    open: true,
    personId: "person.tom",
    phraseIndex: 2,
    currentCaptured: true,
    consentAcknowledged: true,
    localOnly: false,
    captureProvider: "satellite",
    satelliteEntityId: "assist_satellite.office",
    satelliteOptions: [
      { entity_id: "assist_satellite.office", label: "Office Voice Assistant" },
      { entity_id: "assist_satellite.kitchen", label: "Kitchen Voice Assistant" },
    ],
    progressSummary: "2/10 samples, 20%",
    enrollmentSessionId: "session-123",
    completionReadiness: readiness,
    voiceProfileId: "tom_voice",
  });

  const merged = conciergeBuildVoiceEnrollmentDialogState(previous, {
    satelliteOptions: previous.satelliteOptions,
    browserAvailable: false,
    browserSecureContext: true,
    browserMicSupported: true,
    browserStatusSummary: "Browser microphone capture is available.",
  });

  assert.equal(merged.consentAcknowledged, true);
  assert.equal(merged.captureProvider, "satellite");
  assert.equal(merged.satelliteEntityId, "assist_satellite.office");
  assert.equal(merged.phraseIndex, 2);
  assert.equal(merged.progressSummary, "2/10 samples, 20%");
  assert.equal(merged.enrollmentSessionId, "session-123");
  assert.deepEqual(merged.completionReadiness, readiness);
  assert.equal(merged.voiceProfileId, "tom_voice");
});

test("active voice enrollment modal suppresses hass-driven rerender", () => {
  const app = new ConciergeApp();
  let renderCalls = 0;
  app._loaded = true;
  app._render = () => {
    renderCalls += 1;
  };
  app._voiceEnrollmentDialog = conciergeBuildVoiceEnrollmentDialogState({}, {
    open: true,
    personId: "person.tom",
  });

  app.hass = { auth: { data: {} } };

  assert.equal(renderCalls, 0);
});

test("load keeps person view when person exists without a profile record", async () => {
  const app = new ConciergeApp();
  app._selectedPersonId = "person.tom";
  app._selectedAreaId = null;
  app._selectedCompositeId = null;
  app._render = () => {};
  app._refreshLabelRegistry = async () => {};

  let goHomeCalls = 0;
  app._goHome = () => {
    goHomeCalls += 1;
  };

  app._authFetch = async () => ({
    ok: true,
    json: async () => ({
      areas: [],
      floors: [],
      rooms: {},
      composites: {},
      people: {
        "person.tom": { name: "Tom" },
      },
      person_profiles: {},
      voice_profiles: {},
      room_catalog: {},
      composite_catalog: {},
      global_catalog: {},
      global_features: {},
      global_context_usage: {},
      integration_options: {},
      tts_catalog: {},
      archive_status: {},
      asset_intelligence_connected: false,
    }),
  });

  await app._load();

  assert.equal(goHomeCalls, 0);
  assert.equal(app._selectedPersonId, "person.tom");
});

test("normal hass updates still rerender when no enrollment modal is active", () => {
  const app = new ConciergeApp();
  let renderCalls = 0;
  app._loaded = true;
  app._render = () => {
    renderCalls += 1;
  };

  app.hass = { auth: { data: {} } };

  assert.equal(renderCalls, 1);
});

test("room_devices save maps selected device-group entities into room selection fields", async () => {
  const app = new ConciergeApp();
  const serviceCalls = [];

  app._hass = {
    callService: async (domain, service, payload) => {
      serviceCalls.push({ domain, service, payload });
    },
  };
  app._roomCatalog = {
    "area.kitchen": {
      voice_device_entity_ids: [{ entity_id: "assist_satellite.kitchen" }],
      speaker_entity_ids: [{ entity_id: "media_player.kitchen_speaker" }],
      media_player_entity_ids: [{ entity_id: "media_player.kitchen_speaker" }],
      light_entity_ids: [{ entity_id: "light.kitchen" }],
      lamp_entity_ids: [{ entity_id: "light.kitchen_lamp" }],
      shade_entity_ids: [{ entity_id: "cover.kitchen_shade" }],
      room_sensor_entity_ids: [{ entity_id: "sensor.kitchen_temperature" }],
      room_health_entity_ids: [{ entity_id: "sensor.kitchen_room_health" }],
      human_health_entity_ids: [{ entity_id: "sensor.kitchen_human_health" }],
      tv_entity_ids: [{ entity_id: "media_player.kitchen_tv" }],
      dashboard_entity_ids: [{ entity_id: "sensor.kitchen_dashboard" }],
      other_entity_ids: [{ entity_id: "switch.kitchen_misc" }],
    },
  };
  app._collectRoomDeviceGroups = () => [
    {
      group_name: "Living",
      entity_ids: [
        "assist_satellite.kitchen",
        "media_player.kitchen_speaker",
        "light.kitchen",
        "sensor.unknown",
      ],
    },
  ];
  app._selectedAreaId = null;
  app.querySelector = () => null;
  app._clearRoomSectionDraft = () => {};
  app._clearActiveFormDraft = () => {};
  app._roomDeviceGroupEntityIds = ConciergeApp.prototype._roomDeviceGroupEntityIds;

  await app._saveRoomSection("area.kitchen", "room_devices");

  assert.equal(serviceCalls.length, 1);
  const { domain, service, payload } = serviceCalls[0];
  assert.equal(domain, "concierge");
  assert.equal(service, "update_room_config");
  assert.deepEqual(payload.voice_device_entity_ids, ["assist_satellite.kitchen"]);
  assert.deepEqual(payload.speaker_entity_ids, ["media_player.kitchen_speaker"]);
  assert.deepEqual(payload.media_player_entity_ids, ["media_player.kitchen_speaker"]);
  assert.deepEqual(payload.light_entity_ids, ["light.kitchen"]);
  assert.deepEqual(payload.device_groups, [
    {
      group_name: "Living",
      entity_ids: [
        "assist_satellite.kitchen",
        "media_player.kitchen_speaker",
        "light.kitchen",
        "sensor.unknown",
      ],
    },
  ]);
  assert.deepEqual(payload.other_entity_ids, []);
});

test("merged room save keeps mapped voice and speaker field persistence", async () => {
  const app = new ConciergeApp();
  const serviceCalls = [];

  app._hass = {
    callService: async (domain, service, payload) => {
      serviceCalls.push({ domain, service, payload });
    },
  };
  app._composites = {};
  app._compositeCatalog = {
    "composite.main": {
      voice_device_entity_ids: [{ entity_id: "assist_satellite.main" }],
      speaker_entity_ids: [{ entity_id: "media_player.main_speaker" }],
      media_player_entity_ids: [{ entity_id: "media_player.main_speaker" }],
      light_entity_ids: [{ entity_id: "light.main" }],
      shade_entity_ids: [{ entity_id: "cover.main" }],
      room_sensor_entity_ids: [{ entity_id: "sensor.main" }],
    },
  };
  app._collectRoomDeviceGroups = () => [
    {
      group_name: "Merged",
      entity_ids: ["assist_satellite.main", "media_player.main_speaker", "cover.main"],
    },
  ];
  app.querySelector = () => null;
  app._load = async () => {};
  app._render = () => {};
  app._clearRoomSectionDraft = () => {};
  app._clearActiveFormDraft = () => {};
  app._updateRoomSectionDraftActions = () => {};
  app._roomDeviceGroupEntityIds = ConciergeApp.prototype._roomDeviceGroupEntityIds;

  await app._saveCompositeSection("composite.main", "room_devices");

  assert.equal(serviceCalls.length, 1);
  const { domain, service, payload } = serviceCalls[0];
  assert.equal(domain, "concierge");
  assert.equal(service, "update_composite_config");
  assert.deepEqual(payload.voice_device_entity_ids, ["assist_satellite.main"]);
  assert.deepEqual(payload.speaker_entity_ids, ["media_player.main_speaker"]);
  assert.deepEqual(payload.media_player_entity_ids, ["media_player.main_speaker"]);
  assert.deepEqual(payload.shade_entity_ids, ["cover.main"]);
});

test("capture provider setter ignores unavailable provider selections", () => {
  const app = new ConciergeApp();
  app._voiceEnrollmentDialog = conciergeBuildVoiceEnrollmentDialogState({}, {
    open: true,
    personId: "person.tom",
    captureProvider: "satellite",
    browserAvailable: false,
    satelliteOptions: [{ entity_id: "assist_satellite.office", label: "Office Voice Assistant" }],
  });
  app._render = () => {};

  app._setVoiceEnrollmentCaptureProvider("person.tom", "browser", { render: false });

  assert.equal(app._voiceEnrollmentDialog.captureProvider, "satellite");
});

test("capture button should remain disabled after a phrase is captured until next is selected", () => {
  const app = new ConciergeApp();
  app._archiveStatus = { destination_uri: "/media/NAS/concierge_log", destination_configured: true };
  app._integrationOptions = { capabilities: { cap_voice_enrollment: true } };
  app._peopleRegistry = { "person.tom": { name: "Tom" } };
  app._people = { "person.tom": { voice_profile_id: "tom_voice" } };
  app._voiceProfiles = { tom_voice: { enrollment_state: "untrained", sample_count: 1, consent: {} } };
  app._selectedPersonId = "person.tom";
  app._loaded = true;
  app._loadError = null;
  app._voiceEnrollmentDialog = conciergeBuildVoiceEnrollmentDialogState({}, {
    open: true,
    personId: "person.tom",
    voiceProfileId: "tom_voice",
    currentCaptured: true,
    consentAcknowledged: true,
    localOnly: true,
    captureProvider: "satellite",
    satelliteEntityId: "assist_satellite.office",
    satelliteOptions: [{ entity_id: "assist_satellite.office", label: "Office Voice Assistant" }],
  });
  app._renderPersonDetail("person.tom");

  const markup = String(app.innerHTML || "");
  assert.match(markup, /cg-person-record-voice-phrase[^>]*disabled/);
  assert.doesNotMatch(markup, /cg-person-next-voice-phrase[^>]*disabled/);
});

test("resume enrollment opens the dialog before recovery completes", async () => {
  const app = new ConciergeApp();
  app._integrationOptions = { capabilities: { cap_voice_enrollment: true } };
  app._voiceEnrollmentDialog = conciergeBuildVoiceEnrollmentDialogState({}, { open: false, personId: "" });

  let dialogOpened = false;
  let refreshCalled = false;
  let releaseRecovery;
  const recoveryPending = new Promise((resolve) => {
    releaseRecovery = resolve;
  });

  app._openVoiceEnrollmentDialog = (personId) => {
    dialogOpened = true;
    app._voiceEnrollmentDialog = conciergeBuildVoiceEnrollmentDialogState({}, {
      open: true,
      personId,
      voiceProfileId: "tom_voice",
    });
  };
  app._activeVoiceProfileIdForPerson = () => "tom_voice";
  app._voiceEnrollmentRecoveryAction = async () => {
    await recoveryPending;
    return { recovered: false };
  };
  app._refreshVoiceEnrollmentDialogProgress = async () => {
    refreshCalled = true;
  };
  app._setVoiceEnrollmentStatus = () => {};

  const startPromise = app._startVoiceEnrollment("person.tom");

  assert.equal(dialogOpened, true);
  assert.equal(app._voiceEnrollmentDialog.open, true);
  assert.equal(refreshCalled, false);

  releaseRecovery();
  await startPromise;

  assert.equal(refreshCalled, true);
});

test("satellite capture falls back to progress confirmation when response is incomplete", async () => {
  const app = new ConciergeApp();
  app._archiveStatus = { destination_uri: "/media/NAS/concierge_log", destination_configured: true };
  app._integrationOptions = { capabilities: { cap_voice_enrollment: true } };
  app._peopleRegistry = { "person.tom": { name: "Tom" } };
  app._people = { "person.tom": { voice_profile_id: "tom_voice" } };
  app._voiceProfiles = {
    tom_voice: {
      enrollment_state: "capturing",
      sample_count: 5,
      consent: { voice_enrollment: { consent_acknowledged: true, local_only: true } },
    },
  };
  app._voiceEnrollmentDialog = conciergeBuildVoiceEnrollmentDialogState({}, {
    open: true,
    personId: "person.tom",
    voiceProfileId: "tom_voice",
    phraseIndex: 5,
    currentCaptured: false,
    consentAcknowledged: true,
    localOnly: true,
    captureProvider: "satellite",
    satelliteEntityId: "assist_satellite.office",
    satelliteOptions: [{ entity_id: "assist_satellite.office", label: "Office Voice Assistant" }],
  });

  app._activeVoiceProfileIdForPerson = () => "tom_voice";
  app._syncVoiceEnrollmentDialogOptionsFromDom = () => app._voiceEnrollmentDialog;
  app._ensureVoiceEnrollmentStarted = async () => "tom_voice";
  app._fetchVoiceEnrollmentProgress = async () => ({
    found: true,
    voice_profile_id: "tom_voice",
    progress: {
      sample_count: 6,
      captured_phrase_indices: [5],
      target_sample_count: 10,
      completion_percentage: 75,
      provider_type: "satellite",
      user_safe_status_summary: "Ready to record sample",
    },
  });

  let loadCalled = 0;
  let refreshCalled = 0;
  app._load = async () => {
    loadCalled += 1;
  };
  app._refreshVoiceEnrollmentDialogProgress = async () => {
    refreshCalled += 1;
  };
  app._render = () => {};
  app._hass = {
    callService: async (_domain, service) => {
      if (service === "capture_voice_enrollment_sample") {
        return { sample_registered: false, sample_count: 0 };
      }
      return { ready: false };
    },
    auth: { data: {} },
  };

  await app._captureVoiceEnrollmentSample("person.tom");

  assert.equal(app._voiceEnrollmentDialog.currentCaptured, true);
  assert.match(String(app._voiceEnrollmentDialog.status || ""), /Phrase captured/i);
  assert.equal(loadCalled, 1);
  assert.equal(refreshCalled, 1);
});

test("satellite capture fallback does not mark success when phrase index is not captured", async () => {
  const app = new ConciergeApp();
  app._archiveStatus = { destination_uri: "/media/NAS/concierge_log", destination_configured: true };
  app._integrationOptions = { capabilities: { cap_voice_enrollment: true } };
  app._peopleRegistry = { "person.tom": { name: "Tom" } };
  app._people = { "person.tom": { voice_profile_id: "tom_voice" } };
  app._voiceProfiles = {
    tom_voice: {
      enrollment_state: "capturing",
      sample_count: 10,
      consent: { voice_enrollment: { consent_acknowledged: true, local_only: true } },
    },
  };
  app._voiceEnrollmentDialog = conciergeBuildVoiceEnrollmentDialogState({}, {
    open: true,
    personId: "person.tom",
    voiceProfileId: "tom_voice",
    phraseIndex: 9,
    currentCaptured: false,
    consentAcknowledged: true,
    localOnly: true,
    captureProvider: "satellite",
    satelliteEntityId: "assist_satellite.office",
    satelliteOptions: [{ entity_id: "assist_satellite.office", label: "Office Voice Assistant" }],
  });

  app._activeVoiceProfileIdForPerson = () => "tom_voice";
  app._syncVoiceEnrollmentDialogOptionsFromDom = () => app._voiceEnrollmentDialog;
  app._ensureVoiceEnrollmentStarted = async () => "tom_voice";
  app._fetchVoiceEnrollmentProgress = async () => ({
    found: true,
    voice_profile_id: "tom_voice",
    progress: {
      sample_count: 10,
      captured_phrase_indices: [0, 1, 2, 3, 4, 5, 6, 7, 8],
      target_sample_count: 10,
      completion_percentage: 100,
      provider_type: "satellite",
      user_safe_status_summary: "Ready to record sample",
    },
  });
  app._load = async () => {};
  app._refreshVoiceEnrollmentDialogProgress = async () => {};
  app._render = () => {};
  app._hass = {
    callService: async (_domain, service) => {
      if (service === "capture_voice_enrollment_sample") {
        return {
          sample_registered: false,
          sample_count: 10,
          captured_phrase_indices: [0, 1, 2, 3, 4, 5, 6, 7, 8],
        };
      }
      return { ready: false };
    },
    auth: { data: {} },
  };

  await app._captureVoiceEnrollmentSample("person.tom");

  assert.equal(app._voiceEnrollmentDialog.currentCaptured, false);
  assert.match(String(app._voiceEnrollmentDialog.status || ""), /Satellite capture failed/i);
});

test("build profile button stays enabled so click can perform authoritative readiness check", () => {
  const app = new ConciergeApp();
  app._archiveStatus = { destination_uri: "/media/NAS/concierge_log", destination_configured: true };
  app._integrationOptions = { capabilities: { cap_voice_enrollment: true } };
  app._peopleRegistry = { "person.tom": { name: "Tom" } };
  app._people = { "person.tom": { voice_profile_id: "tom_voice" } };
  app._voiceProfiles = {
    tom_voice: {
      enrollment_state: "capturing",
      sample_count: 10,
      consent: { voice_enrollment: { consent_acknowledged: true, local_only: true } },
    },
  };
  app._selectedPersonId = "person.tom";
  app._loaded = true;
  app._loadError = null;
  app._voiceEnrollmentDialog = conciergeBuildVoiceEnrollmentDialogState({}, {
    open: true,
    personId: "person.tom",
    voiceProfileId: "tom_voice",
    phraseIndex: 9,
    currentCaptured: true,
    consentAcknowledged: true,
    localOnly: true,
    captureProvider: "satellite",
    satelliteEntityId: "assist_satellite.office",
    satelliteOptions: [{ entity_id: "assist_satellite.office", label: "Office Voice Assistant" }],
    completionReadiness: { ready: false, user_safe_status_summary: "Not ready for completion." },
  });

  app._renderPersonDetail("person.tom");
  const markup = String(app.innerHTML || "");

  assert.doesNotMatch(markup, /cg-person-next-voice-phrase[^>]*disabled/);
});

test("busy banner is shown and dialog actions are disabled while backend verification is in progress", () => {
  const app = new ConciergeApp();
  app._archiveStatus = { destination_uri: "/media/NAS/concierge_log", destination_configured: true };
  app._integrationOptions = { capabilities: { cap_voice_enrollment: true } };
  app._peopleRegistry = { "person.tom": { name: "Tom" } };
  app._people = { "person.tom": { voice_profile_id: "tom_voice" } };
  app._voiceProfiles = {
    tom_voice: {
      enrollment_state: "capturing",
      sample_count: 10,
      consent: { voice_enrollment: { consent_acknowledged: true, local_only: true } },
    },
  };
  app._selectedPersonId = "person.tom";
  app._loaded = true;
  app._loadError = null;
  app._voiceEnrollmentDialog = conciergeBuildVoiceEnrollmentDialogState({}, {
    open: true,
    personId: "person.tom",
    voiceProfileId: "tom_voice",
    phraseIndex: 9,
    currentCaptured: true,
    consentAcknowledged: true,
    localOnly: true,
    captureProvider: "satellite",
    satelliteEntityId: "assist_satellite.office",
    satelliteOptions: [{ entity_id: "assist_satellite.office", label: "Office Voice Assistant" }],
    isBusy: true,
    busyLabel: "Checking completion readiness with backend...",
    completionReadiness: null,
    progress: { sample_count: 10, target_sample_count: 10 },
  });

  app._renderPersonDetail("person.tom");
  const markup = String(app.innerHTML || "");

  assert.match(markup, /cg-voice-busy-banner/);
  assert.match(markup, /Checking completion readiness with backend/);
  assert.match(markup, /cg-person-voice-dialog-close[^>]*disabled/);
  assert.match(markup, /cg-person-record-voice-phrase[^>]*disabled/);
  assert.match(markup, /cg-person-next-voice-phrase[^>]*disabled/);
  assert.match(markup, /Checking completion readiness/);
});

test("completion status shows backend reason code when readiness is false", () => {
  const app = new ConciergeApp();
  const summary = app._voiceEnrollmentCompletionStatus({
    completionReadiness: {
      ready: false,
      reason_code: "session_missing",
      user_safe_status_summary: "Enrollment is not ready for completion.",
    },
  });

  assert.equal(summary, "Enrollment is not ready for completion. [session_missing]");
});

test("readiness normalization unwraps nested response payloads", () => {
  const app = new ConciergeApp();

  const normalized = app._normalizeVoiceEnrollmentReadiness({
    response: {
      result: {
        ready: false,
        reason_code: "session_missing",
        user_safe_status_summary: "Enrollment is not ready for completion.",
      },
    },
  });

  assert.equal(normalized.ready, false);
  assert.equal(normalized.reason_code, "session_missing");
});