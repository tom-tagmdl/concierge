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
    this._globalCatalog = {
      weather_entity_ids: [],
      news_entity_ids: [],
      alarm_entity_ids: [],
    };
    this._globalFeatures = {};
    this._globalContextUsage = {};
    this._assetIntelligenceConnected = false;
    this._mergeMode = false;
    this._mergeDraftName = "";
    this._mergeDraftAreaIds = [];
    this._editMergeCompositeId = null;
    this._editMergeName = "";
    this._editMergeAreaIds = [];
    this._editMergeError = "";
    this._editMergeDelegatesBound = false;
    this._selectedAreaId = null;
    this._selectedCompositeId = null;
    this._selectedPersonId = null;
  }

  connectedCallback() {
    this._selectedAreaId = null;
    this._selectedCompositeId = null;
    this._selectedPersonId = null;
    if (!this._editMergeDelegatesBound) {
      this._editMergeDelegatesBound = true;
      this.addEventListener("click", (event) => {
        const target = event.target instanceof Element ? event.target : null;
        if (!target) return;

        const openButton = target.closest("[data-edit-merge-open]");
        if (openButton) {
          event.preventDefault();
          event.stopPropagation();
          const compositeId = openButton.getAttribute("data-composite-id");
          if (compositeId) this._openEditMergeDialog(compositeId);
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
      });

      this.addEventListener("change", (event) => {
        const target = event.target instanceof Element ? event.target : null;
        if (!target) return;

        if (target.matches(".cg-edit-merge-room")) {
          this._editMergeError = "";
          this._syncEditMergeSelectionFromDom();
        }
      });
    }
  }

  disconnectedCallback() {
    // no-op
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
    if (!this._loaded && !this._loadingPromise) {
      this._loadingPromise = this._load().finally(() => {
        this._loadingPromise = null;
      });
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
    this._renderStartupLoading();
    try {
      const [areas, floors, snapshotResponse] = await Promise.all([
        this._hass.callWS({ type: "config/area_registry/list" }),
        this._hass.callWS({ type: "config/floor_registry/list" }),
        this._authFetch("/api/concierge/storage_snapshot"),
      ]);

      if (!snapshotResponse.ok) throw new Error(`HTTP ${snapshotResponse.status}`);
      const snapshot = await snapshotResponse.json();

      this._areas = Array.isArray(areas)
        ? areas.map((area) => ({
          ...area,
          id: area?.id || area?.area_id || area?.areaId || "",
        }))
        : [];
      this._floors = Array.isArray(floors) ? floors : [];
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
      this._assetIntelligenceConnected = Boolean(snapshot.asset_intelligence_connected);
      this._loadError = null;

      if (this._selectedAreaId && !this._areas.find((area) => area.id === this._selectedAreaId)) {
        this._goHome();
      }
      if (this._selectedCompositeId && !this._composites[this._selectedCompositeId]) {
        this._goHome();
      }
      if (this._selectedPersonId && !this._people[this._selectedPersonId]) {
        this._goHome();
      }
    } catch (err) {
      this._loadError = err instanceof Error ? err.message : String(err);
    }
    this._loaded = true;
    this._render();
  }

  async _authFetch(url) {
    const token = this._hass?.auth?.data?.access_token;
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    return fetch(url, {
      method: "GET",
      credentials: "same-origin",
      headers,
    });
  }

  _openRoom(areaId) {
    if (!areaId) return;
    this._selectedCompositeId = null;
    this._selectedPersonId = null;
    this._selectedAreaId = areaId;
    this._render();
  }

  _openComposite(compositeId) {
    if (!compositeId) return;
    this._selectedAreaId = null;
    this._selectedPersonId = null;
    this._selectedCompositeId = compositeId;
    this._render();
  }

  _openPerson(personId) {
    if (!personId) return;
    this._selectedAreaId = null;
    this._selectedCompositeId = null;
    this._selectedPersonId = personId;
    this._render();
  }

  _goHome() {
    this._selectedAreaId = null;
    this._selectedCompositeId = null;
    this._selectedPersonId = null;
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

  _escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  _selectedIds(room, key) {
    const value = room?.[key];
    return Array.isArray(value) ? value : [];
  }

  _collectSelected(selectElement) {
    if (!selectElement) return [];
    return Array.from(selectElement.selectedOptions || []).map((item) => item.value).filter(Boolean);
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

  _mergedGlobalConfig(key) {
    return this._globalFeatures[key] || this._globalContextUsage[key] || { enabled: false, options: {} };
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

    pushIfAvailable("light_entity_ids", "Lights and Lamps", roomCatalog.light_entity_ids);
    pushIfAvailable("speaker_entity_ids", "Speakers", roomCatalog.speaker_entity_ids);
    pushIfAvailable("voice_device_entity_ids", "Voice Assistants", roomCatalog.voice_device_entity_ids);
    pushIfAvailable("shade_entity_ids", "Shades", roomCatalog.shade_entity_ids);
    pushIfAvailable("room_sensor_entity_ids", "Room Sensors", roomCatalog.room_sensor_entity_ids);

    if (this._assetIntelligenceConnected) {
      pushIfAvailable("asset_entity_ids", "Asset Intelligence Assets", roomCatalog.asset_entity_ids);
      pushIfAvailable("room_health_entity_ids", "Room Environment (Asset Intelligence)", roomCatalog.room_health_entity_ids);
      pushIfAvailable("human_health_entity_ids", "Human Health (Asset Intelligence)", roomCatalog.human_health_entity_ids);
    }

    pushIfAvailable("dashboard_entity_ids", "Dashboards", roomCatalog.dashboard_entity_ids);
    pushIfAvailable("media_player_entity_ids", "Media Players", roomCatalog.speaker_entity_ids);
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
      <div class="cg-modal-backdrop">
        <div class="cg-modal" role="dialog" aria-modal="true" aria-labelledby="cg-edit-merge-title">
          <div class="cg-modal-head">
            <div>
              <div class="cg-modal-title" id="cg-edit-merge-title">Edit Merge</div>
              <div class="cg-modal-copy">Update the composite name and member rooms.</div>
            </div>
            <button type="button" class="cg-modal-close" data-edit-merge-close aria-label="Close edit dialog">×</button>
          </div>
          <div class="cg-modal-body">
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
          <div class="cg-modal-actions">
            <button type="button" class="cg-modal-cancel" data-edit-merge-cancel>Cancel</button>
            <button type="button" class="cg-modal-update" data-edit-merge-update>Update</button>
          </div>
        </div>
      </div>
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
    const categoryFieldKeys = [
      "asset_entity_ids",
      "room_sensor_entity_ids",
      "room_health_entity_ids",
      "human_health_entity_ids",
      "light_entity_ids",
      "shade_entity_ids",
      "speaker_entity_ids",
      "voice_device_entity_ids",
      "dashboard_entity_ids",
      "media_player_entity_ids",
      "other_entity_ids",
    ];

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
      };
      categoryFieldKeys.forEach((fieldKey) => {
        const selectEl = this.querySelector(
          `select[data-area-id="${CSS.escape(compositeId)}"][data-field-key="${CSS.escape(fieldKey)}"]`
        );
        payload[fieldKey] = this._collectSelected(selectEl);
      });
      await this._hass.callService(
        "concierge",
        "update_composite_config",
        payload,
        undefined,
        true,
        true
      );
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

  async _saveGlobalSettings() {
    const weatherEntityId = this.querySelector("#cg-weather-entity")?.value || "";
    const newsEntityId = this.querySelector("#cg-news-entity")?.value || "";
    const alarmEntityId = this.querySelector("#cg-alarm-entity")?.value || "";
    const alarmActionsEnabled = Boolean(this.querySelector("#cg-alarm-actions")?.checked);

    const status = this.querySelector(".cg-global-status");
    if (status) status.textContent = "Saving global settings...";

    try {
      await this._hass.callService("concierge", "update_global_context", {
        context_type: "weather",
        enabled: Boolean(weatherEntityId),
        options: weatherEntityId ? { entity_id: weatherEntityId } : {},
      });
      await this._hass.callService("concierge", "update_global_context", {
        context_type: "news",
        enabled: Boolean(newsEntityId),
        options: newsEntityId ? { entity_id: newsEntityId } : {},
      });
      await this._hass.callService("concierge", "update_global_context", {
        context_type: "alarm_status",
        enabled: Boolean(alarmEntityId),
        options: alarmEntityId ? { entity_id: alarmEntityId, allow_actions: alarmActionsEnabled } : {},
      });
      if (status) status.textContent = "Saved";
    } catch (err) {
      if (status) status.textContent = `Save failed: ${err?.message || err}`;
    }
  }

  async _saveRoomConfig(areaId) {
    const getSelect = (fieldKey) => this.querySelector(`select[data-area-id="${CSS.escape(areaId)}"][data-field-key="${CSS.escape(fieldKey)}"]`);
    const postureSelect = this.querySelector(`select[data-area-id="${CSS.escape(areaId)}"][data-field-key="posture"]`);

    const payload = {
      area_id: areaId,
      posture: postureSelect ? postureSelect.value : "day",
      media_player_entity_ids: this._collectSelected(getSelect("media_player_entity_ids")),
      voice_device_entity_ids: this._collectSelected(getSelect("voice_device_entity_ids")),
      asset_entity_ids: this._collectSelected(getSelect("asset_entity_ids")),
      room_sensor_entity_ids: this._collectSelected(getSelect("room_sensor_entity_ids")),
      room_health_entity_ids: this._collectSelected(getSelect("room_health_entity_ids")),
      human_health_entity_ids: this._collectSelected(getSelect("human_health_entity_ids")),
      light_entity_ids: this._collectSelected(getSelect("light_entity_ids")),
      shade_entity_ids: this._collectSelected(getSelect("shade_entity_ids")),
      speaker_entity_ids: this._collectSelected(getSelect("speaker_entity_ids")),
      dashboard_entity_ids: this._collectSelected(getSelect("dashboard_entity_ids")),
      other_entity_ids: this._collectSelected(getSelect("other_entity_ids")),
      persona: this.querySelector(`input[data-area-id="${CSS.escape(areaId)}"][data-field-key="persona"]`)?.value || "",
      persona_prompt: this.querySelector(`textarea[data-area-id="${CSS.escape(areaId)}"][data-field-key="persona_prompt"]`)?.value || "",
    };

    const status = this.querySelector(`.cg-room-status[data-area-id="${CSS.escape(areaId)}"]`);
    if (status) status.textContent = "Saving room...";
    try {
      await this._hass.callService("concierge", "update_room_config", payload);
      if (status) status.textContent = "Saved";
    } catch (err) {
      if (status) status.textContent = `Save failed: ${err?.message || err}`;
    }
  }

  async _savePersonProfile(personId) {
    const field = (fieldKey) => this.querySelector(`[data-person-id="${CSS.escape(personId)}"][data-field-key="${CSS.escape(fieldKey)}"]`);
    const status = this.querySelector(`.cg-person-status[data-person-id="${CSS.escape(personId)}"]`);
    const consentText = field("consent")?.value || "{}";
    let consent = {};
    try {
      consent = consentText.trim() ? JSON.parse(consentText) : {};
    } catch (err) {
      if (status) status.textContent = `Consent JSON must be valid: ${err?.message || err}`;
      return;
    }

    const payload = {
      person_id: personId,
      name: field("name")?.value || "",
      linked_area_id: field("linked_area_id")?.value || undefined,
      voice_profile_id: field("voice_profile_id")?.value || undefined,
      ble_device_ids: (field("ble_device_ids")?.value || "").split(/\r?\n/).map((item) => item.trim()).filter(Boolean),
      aqara_presence_entity_ids: (field("aqara_presence_entity_ids")?.value || "").split(/\r?\n/).map((item) => item.trim()).filter(Boolean),
      consent,
      notes: field("notes")?.value || "",
    };

    if (status) status.textContent = "Saving person...";
    try {
      await this._hass.callService("concierge", "update_person_profile", payload);
      if (status) status.textContent = "Saved";
      await this._load();
    } catch (err) {
      if (status) status.textContent = `Save failed: ${err?.message || err}`;
    }
  }

  _bindEvents() {
    this.querySelectorAll("button[data-nav='home']").forEach((button) => {
      button.addEventListener("click", () => this._goHome());
    });

    this.querySelectorAll("button[data-nav-room]").forEach((button) => {
      const areaId = button.getAttribute("data-nav-room");
      button.addEventListener("click", () => {
        if (areaId) this._openRoom(areaId);
      });
    });

    const globalSaveButton = this.querySelector(".cg-save-global");
    if (globalSaveButton) {
      globalSaveButton.addEventListener("click", () => this._saveGlobalSettings());
    }

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

    this.querySelectorAll(".cg-apply-ble-suggestions").forEach((button) => {
      button.addEventListener("click", () => {
        const personId = button.getAttribute("data-person-id");
        if (!personId) return;
        const person = this._peopleRegistry[personId];
        const suggestions = Array.isArray(person?.ble_device_suggestions) ? person.ble_device_suggestions : [];
        const field = this.querySelector(`[data-person-id="${CSS.escape(personId)}"][data-field-key="ble_device_ids"]`);
        if (field) {
          field.value = suggestions.join("\n");
        }
      });
    });

    this.querySelectorAll(".cg-save-room").forEach((button) => {
      button.addEventListener("click", () => {
        const areaId = button.getAttribute("data-area-id");
        if (areaId) this._saveRoomConfig(areaId);
      });
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
    const floorMap = {};
    this._floors.forEach((floor) => {
      if (floor && floor.floor_id) floorMap[floor.floor_id] = floor;
    });

    const grouped = {};
    for (const area of this._areas) {
      const floorId = area?.floor_id || null;
      const floorName = floorId && floorMap[floorId] ? floorMap[floorId].name : "Unassigned";
      if (!grouped[floorName]) grouped[floorName] = [];
      grouped[floorName].push(area);
    }

    const floorOrder = Object.keys(grouped).sort((a, b) => String(a).localeCompare(String(b)));

    const weatherCfg = this._mergedGlobalConfig("weather");
    const newsCfg = this._mergedGlobalConfig("news");
    const alarmCfg = this._mergedGlobalConfig("alarm_status");

    const weatherEntityId = weatherCfg?.options?.entity_id || "";
    const newsEntityId = newsCfg?.options?.entity_id || "";
    const alarmEntityId = alarmCfg?.options?.entity_id || "";
    const alarmActionsEnabled = Boolean(alarmCfg?.options?.allow_actions);
    const people = Object.values(this._peopleRegistry || {}).sort((left, right) => String(left?.name || left?.entity_id || "").localeCompare(String(right?.name || right?.entity_id || "")));
    const peopleMarkup = people.length
      ? people.map((person) => {
          const personId = person.entity_id || "";
          const profile = this._people[personId] || {};
          const voiceProfile = profile.voice_profile_id ? this._voiceProfiles[profile.voice_profile_id] : null;
          const voiceLabel = voiceProfile?.name || profile.voice_profile_id || "Not set";
          const deviceTrackers = Array.isArray(person.device_trackers) ? person.device_trackers : [];
          const inZones = Array.isArray(person.in_zones) ? person.in_zones : [];
          const entityPicture = person.entity_picture || "";
          return `
            <div class="cg-room-card cg-person-click" data-person-id="${this._escapeHtml(personId)}" role="button" tabindex="0" aria-label="Open profile for ${this._escapeHtml(person.name || personId)}">
              ${entityPicture ? `<img class="cg-room-image" src="${this._escapeHtml(entityPicture)}" alt="${this._escapeHtml(person.name || personId)}">` : ""}
              <div class="cg-room-head">
                <div class="cg-room-name">${this._escapeHtml(person.name || personId)}</div>
                <button type="button" class="cg-room-action" data-person-id="${this._escapeHtml(personId)}">Edit Person</button>
              </div>
              <div class="cg-room-meta">State: ${this._escapeHtml(person.state || "unknown")}</div>
              <div class="cg-room-meta">Tracked devices: ${deviceTrackers.length}</div>
              <div class="cg-room-meta">In zones: ${inZones.length}</div>
              <div class="cg-room-meta">Voice profile: ${this._escapeHtml(voiceLabel)}</div>
            </div>
          `;
        }).join("")
      : `<div class="cg-muted">No people profiles have been created yet.</div>`;
    const voiceProfiles = Object.values(this._voiceProfiles || {}).sort((left, right) => String(left?.name || left?.voice_profile_id || "").localeCompare(String(right?.name || right?.voice_profile_id || "")));
    const voiceProfilesMarkup = voiceProfiles.length
      ? voiceProfiles.map((profile) => `
          <div class="cg-room-card">
            <div class="cg-room-head">
              <div class="cg-room-name">${this._escapeHtml(profile.name || profile.voice_profile_id || "Voice Profile")}</div>
            </div>
            <div class="cg-room-meta">TTS voice: ${this._escapeHtml(profile.tts_voice || "Not set")}</div>
            <div class="cg-room-meta">Enrollment state: ${this._escapeHtml(profile.enrollment_state || "untrained")}</div>
            <div class="cg-room-meta">Samples: ${this._escapeHtml(String(profile.sample_count ?? 0))}</div>
          </div>
        `).join("")
      : `<div class="cg-muted">No voice profiles have been created yet.</div>`;

    const enabledComposites = Object.values(this._composites || {})
      .filter((item) => item && item.enabled !== false && Array.isArray(item.area_ids) && item.area_ids.length > 0);
    const memberAreaIds = new Set(enabledComposites.flatMap((item) => item.area_ids || []));

    const compositesByFloor = {};
    enabledComposites.forEach((composite) => {
      const firstAreaId = (composite.area_ids || [])[0];
      const firstArea = this._areas.find((area) => area.id === firstAreaId);
      const floorName = firstArea?.floor_id && floorMap[firstArea.floor_id]
        ? floorMap[firstArea.floor_id].name
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
              <div class="cg-room-meta">Voice Assistant: Not set</div>
              <div class="cg-room-meta">Primary Speakers: Not set</div>
              <div class="cg-room-meta">Persona: Not set</div>
              <div class="cg-row-end" style="margin-top: 8px;">
                <a href="#" class="cg-composite-link" data-composite-id="${this._escapeHtml(compositeId)}">Configure room</a>
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
        .cg-global { border-radius: 16px; padding: 18px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,0.08)); margin-bottom: 16px; }
        .cg-global-title { font-size: 16px; font-weight: 600; margin-bottom: 6px; }
        .cg-global-copy { color: var(--secondary-text-color); font-size: 13px; }
        .cg-global-grid { display: grid; gap: 12px; margin-top: 12px; }
        .cg-global-item label { display: block; font-size: 13px; color: var(--secondary-text-color); margin-bottom: 4px; }
        .cg-global-item select { min-height: 36px; width: 100%; }
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
        <div class="cg-head">
          <img class="cg-logo" src="${this._logoSrc()}" alt="Concierge">
          <div>
            <div class="cg-title">Concierge</div>
            <div class="cg-subtitle">Global settings and room configuration status</div>
          </div>
        </div>

        ${this._renderBreadcrumb([{ label: "Home Assistant" }, { label: "Concierge" }])}

        <div class="cg-global">
          <div class="cg-global-title">Global Settings</div>
          <div class="cg-global-copy">Available options are based on installed integrations. Blank means no integration is currently available for that category.</div>
          <div class="cg-global-grid">
            <div class="cg-global-item">
              <label for="cg-weather-entity">Outside Weather</label>
              ${this._renderCategorySelect("cg-weather-entity", this._globalCatalog.weather_entity_ids, weatherEntityId, "No weather integrations found")}
            </div>
            <div class="cg-global-item">
              <label for="cg-news-entity">News</label>
              ${this._renderCategorySelect("cg-news-entity", this._globalCatalog.news_entity_ids, newsEntityId, "No news integrations found")}
            </div>
            <div class="cg-global-item">
              <label for="cg-alarm-entity">Alarm Status</label>
              ${this._renderCategorySelect("cg-alarm-entity", this._globalCatalog.alarm_entity_ids, alarmEntityId, "No alarm integrations found")}
            </div>
            <div class="cg-global-item">
              <label>
                <input id="cg-alarm-actions" type="checkbox" ${alarmActionsEnabled ? "checked" : ""}>
                Allow Concierge to take alarm actions
              </label>
            </div>
          </div>
          <div class="cg-row-end" style="margin-top: 12px;">
            <button class="cg-save-global">Save Global Settings</button>
            <span class="cg-global-status"></span>
          </div>
        </div>

        <div class="cg-rooms-title">People</div>
        <div class="cg-global" style="margin-bottom: 12px;">
          <div class="cg-global-title">People Setup</div>
          <div class="cg-global-copy">People profiles hold consent, device bindings, and voice attribution state.</div>
          <div class="cg-grid" style="margin-top: 12px;">${peopleMarkup}</div>
        </div>

        <div class="cg-global" style="margin-bottom: 12px;">
          <div class="cg-global-title">Voice Profiles</div>
          <div class="cg-global-copy">Voice enrollment is tracked separately from person bindings.</div>
          <div class="cg-grid" style="margin-top: 12px;">${voiceProfilesMarkup}</div>
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

    const room = this._rooms[areaId] || {};
    const catalog = this._roomCatalog[areaId] || {};
    const cards = this._availableRoomCards(catalog);
    const posture = room.posture || "day";
    const postureOptions = ["day", "evening", "night", "sleep", "away"]
      .map((item) => `<option value="${item}"${item === posture ? " selected" : ""}>${item.charAt(0).toUpperCase() + item.slice(1)}</option>`)
      .join("");

    const cardsMarkup = cards.length
      ? cards.map((card) => `
        <div class="cg-config-card">
          <div class="cg-config-title">${this._escapeHtml(card.title)}</div>
          ${this._renderMultiSelect(areaId, card.fieldKey, "Select entities", card.options, this._selectedIds(room, card.fieldKey))}
        </div>
      `).join("")
      : `<div class="cg-muted">No configurable integration options are currently available for this room.</div>`;

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
        .cg-layout { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
        .cg-config-card { border-radius: 16px; padding: 14px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,0.08)); }
        .cg-config-title { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
        .cg-field { display: grid; gap: 4px; }
        .cg-field label { font-size: 12px; color: var(--secondary-text-color); }
        .cg-field select, .cg-field input, .cg-field textarea { min-height: 34px; width: 100%; }
        .cg-multi { min-height: 96px !important; }
        .cg-row-end { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
        .cg-save-room { border: 0; border-radius: 10px; padding: 8px 12px; background: var(--primary-color); color: #fff; cursor: pointer; font-weight: 600; }
        .cg-room-status { font-size: 12px; color: var(--secondary-text-color); }
        .cg-muted { color: var(--secondary-text-color); font-size: 13px; }
      </style>
      <div class="cg-shell">
        <div class="cg-head">
          <img class="cg-logo" src="${this._logoSrc()}" alt="Concierge">
          <div>
            <div class="cg-title">${this._escapeHtml(area.name || area.id)}</div>
            <div class="cg-subtitle">Room configuration</div>
          </div>
        </div>

        ${this._renderBreadcrumb([
          { label: "Concierge", nav: "home" },
          { label: area.name || area.id, roomId: areaId },
        ])}

        <div class="cg-config-card" style="margin-top:14px; margin-bottom:14px;">
          <div class="cg-config-title">Voice Personality</div>
          <div class="cg-field">
            <label>Persona Name</label>
            <input type="text" data-area-id="${this._escapeHtml(areaId)}" data-field-key="persona" value="${this._escapeHtml(room.persona || "")}">
          </div>
          <div class="cg-field" style="margin-top: 10px;">
            <label>Persona Paragraph</label>
            <textarea data-area-id="${this._escapeHtml(areaId)}" data-field-key="persona_prompt" rows="5">${this._escapeHtml(room.persona_prompt || "")}</textarea>
          </div>
        </div>

        <div class="cg-config-card" style="margin-top:14px; margin-bottom:14px;">
          <div class="cg-config-title">Room Posture</div>
          <div class="cg-field">
            <label>Select posture</label>
            <select data-area-id="${this._escapeHtml(areaId)}" data-field-key="posture">${postureOptions}</select>
          </div>
        </div>

        <div class="cg-layout">
          ${cardsMarkup}
        </div>

        <div class="cg-row-end">
          <button class="cg-save-room" data-area-id="${this._escapeHtml(areaId)}">Save Room Configuration</button>
          <span class="cg-room-status" data-area-id="${this._escapeHtml(areaId)}"></span>
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
    const nameValue = profile.name || personName;
    const selectedVoiceProfile = profile.voice_profile_id ? this._voiceProfiles[profile.voice_profile_id] : null;
    const bleSuggestions = Array.isArray(person.ble_device_suggestions) ? person.ble_device_suggestions : [];
    const bleSuggestionSources = person.ble_device_suggestion_sources || {};

    const areaOptions = this._areas
      .slice()
      .sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")))
      .map((area) => {
        const selected = area.id === profile.linked_area_id ? " selected" : "";
        return `<option value="${this._escapeHtml(area.id)}"${selected}>${this._escapeHtml(area.name || area.id)}</option>`;
      })
      .join("");

    const voiceOptions = Object.values(this._voiceProfiles || {})
      .slice()
      .sort((left, right) => String(left.name || "").localeCompare(String(right.name || "")))
      .map((profile) => {
        const selected = profile.voice_profile_id === person.voice_profile_id ? " selected" : "";
        return `<option value="${this._escapeHtml(profile.voice_profile_id)}"${selected}>${this._escapeHtml(profile.name || profile.voice_profile_id)}</option>`;
      })
      .join("");

    const voiceProfilesMarkup = Object.values(this._voiceProfiles || {})
      .slice()
      .sort((left, right) => String(left.name || left.voice_profile_id || "").localeCompare(String(right.name || right.voice_profile_id || "")))
      .map((voiceProfile) => {
        const isSelected = voiceProfile.voice_profile_id === profile.voice_profile_id;
        const ttsVoice = voiceProfile.tts_voice || "Not set";
        const enrollmentState = voiceProfile.enrollment_state || "untrained";
        const sampleCount = String(voiceProfile.sample_count ?? 0);
        return `
          <div class="cg-room-card${isSelected ? " cg-voice-selected" : ""}">
            <div class="cg-room-head">
              <div class="cg-room-name">${this._escapeHtml(voiceProfile.name || voiceProfile.voice_profile_id || "Voice Profile")}</div>
            </div>
            <div class="cg-room-meta">TTS voice: ${this._escapeHtml(ttsVoice)}</div>
            <div class="cg-room-meta">Enrollment state: ${this._escapeHtml(enrollmentState)}</div>
            <div class="cg-room-meta">Samples: ${this._escapeHtml(sampleCount)}</div>
          </div>
        `;
      })
      .join("");

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
    const consentValue = JSON.stringify(profile.consent || {}, null, 2);

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
        .cg-config-card { border-radius: 16px; padding: 14px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,0.08)); }
        .cg-config-title { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
        .cg-field { display: grid; gap: 4px; }
        .cg-field label { font-size: 12px; color: var(--secondary-text-color); }
        .cg-field select, .cg-field input, .cg-field textarea { min-height: 34px; width: 100%; }
        .cg-voice-library { margin-top: 14px; display: grid; gap: 12px; }
        .cg-voice-selected { border: 1px solid var(--primary-color); }
        .cg-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px; }
        .cg-ble-suggestions { margin-top: 14px; display: grid; gap: 8px; }
        .cg-apply-ble-suggestions { border: 0; border-radius: 10px; padding: 8px 12px; background: color-mix(in srgb, var(--primary-color) 14%, transparent); color: var(--primary-color); cursor: pointer; font-weight: 700; }
        .cg-muted { color: var(--secondary-text-color); font-size: 13px; }
        .cg-row-end { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
        .cg-save-person { border: 0; border-radius: 10px; padding: 8px 12px; background: var(--primary-color); color: #fff; cursor: pointer; font-weight: 600; }
        .cg-person-status { font-size: 12px; color: var(--secondary-text-color); }
      </style>
      <div class="cg-shell">
        <div class="cg-head">
          <img class="cg-logo" src="${this._logoSrc()}" alt="Concierge">
          <div>
            <div class="cg-title">${this._escapeHtml(personName)}</div>
            <div class="cg-subtitle">Person configuration</div>
          </div>
        </div>

        ${this._renderBreadcrumb([
          { label: "Concierge", nav: "home" },
          { label: personName },
        ])}

        <div class="cg-config-card" style="margin-top:14px; margin-bottom:14px;">
          <div class="cg-config-title">Person Identity</div>
          <div class="cg-field">
            <label>Person Name</label>
            <input type="text" data-person-id="${this._escapeHtml(personId)}" data-field-key="name" value="${this._escapeHtml(nameValue)}">
          </div>
          <div class="cg-field" style="margin-top: 10px;">
            <label>Linked Area</label>
            <select data-person-id="${this._escapeHtml(personId)}" data-field-key="linked_area_id">
              <option value="">Not set</option>
              ${areaOptions}
            </select>
          </div>
          <div class="cg-field" style="margin-top: 10px;">
            <label>Voice Profile</label>
            <select data-person-id="${this._escapeHtml(personId)}" data-field-key="voice_profile_id">
              <option value="">Not set</option>
              ${voiceOptions}
            </select>
          </div>
          <div class="cg-voice-library">
            <div class="cg-config-title">Voice Profiles</div>
            <div class="cg-muted">Browse the available voice profiles while editing this person. The selected profile is highlighted below.</div>
            <div class="cg-grid" style="margin-top: 4px;">
              ${voiceProfilesMarkup || `<div class="cg-muted">No voice profiles have been created yet.</div>`}
            </div>
            ${selectedVoiceProfile ? `<div class="cg-muted">Selected profile: ${this._escapeHtml(selectedVoiceProfile.name || selectedVoiceProfile.voice_profile_id || "Voice Profile")}</div>` : ""}
          </div>
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
          <div class="cg-field" style="margin-top: 10px;">
            <label>Consent JSON</label>
            <textarea data-person-id="${this._escapeHtml(personId)}" data-field-key="consent" rows="6">${this._escapeHtml(consentValue)}</textarea>
          </div>
          <div class="cg-field" style="margin-top: 10px;">
            <label>Notes</label>
            <textarea data-person-id="${this._escapeHtml(personId)}" data-field-key="notes" rows="3">${this._escapeHtml(profile.notes || "")}</textarea>
          </div>
        </div>

        <div class="cg-row-end">
          <button class="cg-save-person" data-person-id="${this._escapeHtml(personId)}">Save Person Profile</button>
          <span class="cg-person-status" data-person-id="${this._escapeHtml(personId)}"></span>
        </div>
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
    const memberNames = this._memberAreaNames(areaIds);
    const firstArea = this._areas.find((item) => item.id === areaIds[0]);
    const floorId = firstArea?.floor_id || null;
    const floorLabel = this._floors.find((item) => item.floor_id === floorId)?.name || "Unassigned";

    const floorAreas = this._areas
      .filter((item) => (item.floor_id || null) === floorId)
      .sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")));

    const areaOptions = floorAreas
      .map((area) => {
        const selected = areaIds.includes(area.id) ? " selected" : "";
        return `<option value="${this._escapeHtml(area.id)}"${selected}>${this._escapeHtml(area.name || area.id)}</option>`;
      })
      .join("");

    const cards = this._availableRoomCards(this._compositeCatalog[compositeId] || {});
    const cardsMarkup = cards.length
      ? cards.map((card) => `
          <div class="cg-config-card">
            <div class="cg-config-title">${this._escapeHtml(card.title)}</div>
            ${this._renderMultiSelect(
              compositeId,
              card.fieldKey,
              "Aggregated available entities",
              card.options,
              this._selectedIds(composite, card.fieldKey)
            )}
          </div>
        `).join("")
      : `<div class="cg-muted">No aggregated entities detected for this composite.</div>`;

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
        .cg-layout { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
        .cg-config-card { border-radius: 16px; padding: 14px; background: var(--ha-card-background, var(--card-background-color)); box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,0.08)); }
        .cg-config-title { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
        .cg-field { display: grid; gap: 4px; }
        .cg-field label { font-size: 12px; color: var(--secondary-text-color); }
        .cg-field select, .cg-field input { min-height: 34px; width: 100%; }
        .cg-multi { min-height: 96px !important; }
        .cg-row-end { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
        .cg-save-composite { border: 0; border-radius: 10px; padding: 8px 12px; background: var(--primary-color); color: #fff; cursor: pointer; font-weight: 600; }
        .cg-composite-status { font-size: 12px; color: var(--secondary-text-color); }
        .cg-muted { color: var(--secondary-text-color); font-size: 13px; }
      </style>
      <div class="cg-shell">
        <div class="cg-head">
          <img class="cg-logo" src="${this._logoSrc()}" alt="Concierge">
          <div>
            <div class="cg-title">${this._escapeHtml(composite.name || compositeId)}</div>
            <div class="cg-subtitle">Composite configuration</div>
          </div>
        </div>

        ${this._renderBreadcrumb([
          { label: "Concierge", nav: "home" },
          { label: composite.name || compositeId },
        ])}

        <div class="cg-config-card" style="margin-top:14px; margin-bottom:14px;">
          <div class="cg-config-title">Composite Details</div>
          <div class="cg-field">
            <label>Composite Name</label>
            <input id="cg-composite-name-${this._escapeHtml(compositeId)}" type="text" value="${this._escapeHtml(composite.name || compositeId)}">
          </div>
          <div class="cg-field" style="margin-top: 10px;">
            <label>Member Rooms (${this._escapeHtml(floorLabel)} floor)</label>
            <select id="cg-composite-areas-${this._escapeHtml(compositeId)}" multiple class="cg-multi">${areaOptions}</select>
          </div>
          <div class="cg-muted" style="margin-top: 8px;">Current rooms: ${this._escapeHtml(memberNames.join(", ") || "None")}</div>
          <div class="cg-row-end">
            <button class="cg-save-composite" data-composite-id="${this._escapeHtml(compositeId)}">Save Composite</button>
            <span class="cg-composite-status" data-composite-id="${this._escapeHtml(compositeId)}"></span>
          </div>
        </div>

        <div class="cg-muted" style="margin-bottom: 10px;">Available entities aggregated across member rooms.</div>
        <div class="cg-layout">
          ${cardsMarkup}
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
