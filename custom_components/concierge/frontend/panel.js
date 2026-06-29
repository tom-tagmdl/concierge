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
    this._roomCatalog = {};
    this._globalCatalog = {
      weather_entity_ids: [],
      news_entity_ids: [],
      alarm_entity_ids: [],
    };
    this._globalFeatures = {};
    this._globalContextUsage = {};
    this._assetIntelligenceConnected = false;
    this._selectedAreaId = null;
  }

  connectedCallback() {
    this._selectedAreaId = null;
  }

  disconnectedCallback() {
    // no-op
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._loaded && !this._loadingPromise) {
      this._loadingPromise = this._load().finally(() => {
        this._loadingPromise = null;
      });
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

      this._areas = Array.isArray(areas) ? areas : [];
      this._floors = Array.isArray(floors) ? floors : [];
      this._rooms = snapshot.rooms || {};
      this._roomCatalog = snapshot.room_catalog || {};
      this._globalCatalog = snapshot.global_catalog || this._globalCatalog;
      this._globalFeatures = snapshot.global_features || {};
      this._globalContextUsage = snapshot.global_context_usage || {};
      this._assetIntelligenceConnected = Boolean(snapshot.asset_intelligence_connected);
      this._loadError = null;

      if (this._selectedAreaId && !this._areas.find((area) => area.id === this._selectedAreaId)) {
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
    this._selectedAreaId = areaId;
    this._render();
  }

  _goHome() {
    this._selectedAreaId = null;
    this._render();
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

  _configuredCardCount(room, cards) {
    if (!room || !cards.length) return 0;
    return cards.reduce((count, card) => {
      const selected = this._selectedIds(room, card.fieldKey);
      return count + (selected.length ? 1 : 0);
    }, 0);
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

    this.querySelectorAll(".cg-room-link").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const areaId = link.getAttribute("data-area-id");
        if (areaId) this._openRoom(areaId);
      });
    });

    const backButton = this.querySelector(".cg-back-home");
    if (backButton) {
      backButton.addEventListener("click", () => this._goHome());
    }

    this.querySelectorAll(".cg-save-room").forEach((button) => {
      button.addEventListener("click", () => {
        const areaId = button.getAttribute("data-area-id");
        if (areaId) this._saveRoomConfig(areaId);
      });
    });
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

    const roomsMarkup = floorOrder.map((floorName) => {
      const cards = grouped[floorName]
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

          return `
            <div class="cg-room-card cg-room-click" data-area-id="${this._escapeHtml(area.id)}" role="button" tabindex="0" aria-label="Open configuration for ${this._escapeHtml(area.name || area.id)}">
              ${cardImage}
              <div class="cg-room-name">${this._escapeHtml(area.name || area.id)}</div>
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
      return `
        <div class="cg-floor-section">
          <div class="cg-floor-title">${this._escapeHtml(floorName)}</div>
          <div class="cg-grid">${cards}</div>
        </div>
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
        .cg-room-name { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
        .cg-room-meta { font-size: 13px; color: var(--secondary-text-color); line-height: 1.45; }
        .cg-row-end { display: flex; align-items: center; gap: 10px; margin-top: 12px; }
        .cg-open-room, .cg-save-global { border: 0; border-radius: 10px; padding: 8px 12px; background: var(--primary-color); color: #fff; cursor: pointer; font-weight: 600; }
        .cg-room-link { color: var(--primary-color); text-decoration: underline; font-weight: 600; }
        .cg-global-status { font-size: 12px; color: var(--secondary-text-color); }
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

        <div class="cg-rooms-title">Rooms</div>
        ${roomsMarkup}
      </div>
    `;

    this._bindEvents();
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
    this._renderMain();
  }
};

if (!customElements.get("concierge-app")) {
  customElements.define("concierge-app", ConciergeApp);
}
