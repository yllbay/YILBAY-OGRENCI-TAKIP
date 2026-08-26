function topicOptions(){let out="";for(const [c,units] of Object.entries(db.curriculum))for(const topics of Object.values(units))for(const t of topics)out+=`<option data-course="${c}" value="${c}|||${t}">${c} — ${t}</option>`;return out}

/* CELL:40-resources | layer:frontend | generated-from:v0.9.0 */

/* CELL:40-resources | layer:frontend | generated-from:v0.7.2 */
