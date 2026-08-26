/* CELL:130-ui-runtime | layer:frontend | generated-from:v0.7.2 */
function q(id){return document.getElementById(id)}
function modal(html){const d=document.createElement("div");d.className="modalbg";d.id="modalbg";d.innerHTML=`<div class="modal">${html}</div>`;document.body.appendChild(d)}
window.closeModal=()=>document.getElementById("modalbg")?.remove()
window.resetDemo=()=>{db=structuredClone(seed);save();render()}
