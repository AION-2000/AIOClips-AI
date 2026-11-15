"use strict";
const $ = id => document.getElementById(id);
let uploadedAsset = null;
let localPreviewUrl = null;
let exportedBlobUrl = null;

function message(text, isError = false) {
  $("message").textContent = text;
  $("message").className = isError ? "danger" : "";
}
async function request(path, options = {}) {
  const token = $("token").value.trim();
  if (!token) throw new Error("Enter your private studio access token first.");
  const headers = Object.assign({}, options.headers, { Authorization: "Bearer " + token });
  const response = await fetch(path, Object.assign({}, options, { headers, cache: "no-store" }));
  if (!response.ok) {
    let reason;
    try { reason = (await response.json()).detail; } catch (_) { reason = response.statusText; }
    throw new Error(typeof reason === "string" ? reason : JSON.stringify(reason));
  }
  return response;
}
async function json(path, options = {}) {
  return (await request(path, options)).json();
}
async function post(path, body) {
  return json(path, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}
$("videoFile").addEventListener("change", () => {
  const file = $("videoFile").files[0];
  if (localPreviewUrl) URL.revokeObjectURL(localPreviewUrl);
  if (file) {
    localPreviewUrl = URL.createObjectURL(file);
    $("preview").src = localPreviewUrl;
    $("previewNote").textContent = file.name;
  }
});
$("inspectLink").addEventListener("click", async () => {
  try {
    const result = await post("/v1/links", { url: $("url").value.trim() });
    message(result.message + "\n" + result.url);
  } catch (error) { message(error.message, true); }
});
$("upload").addEventListener("click", async () => {
  const file = $("videoFile").files[0];
  if (!file) return message("Select a video file first.", true);
  const button = $("upload");
  button.disabled = true;
  message("Uploading the video. Large recordings may take some time.");
  try {
    const form = new FormData();
    form.append("video", file);
    const uploaded = await json("/v1/uploads", { method: "POST", body: form });
    uploadedAsset = uploaded.asset_id;
    $("uploadInfo").textContent = "Video uploaded · " + uploaded.duration.toFixed(1) + " seconds";
    $("end").value = Math.min(20, uploaded.duration).toFixed(1);
    message("Finding energetic moments. This is a suggestion, not goal recognition.");
    const data = await post("/v1/moments", { asset_id: uploadedAsset, seconds: 20, limit: 5 });
    const parent = $("moments");
    parent.replaceChildren();
    if (!data.moments.length) {
      const caption = document.createElement("small");
      caption.textContent = "No obvious energetic moment found. You can enter start/end times manually.";
      parent.appendChild(caption);
    }
    for (const m of data.moments) {
      const card = document.createElement("div");
      card.className = "moment";
      const text = document.createElement("p");
      text.textContent = m.start.toFixed(1) + "–" + m.end.toFixed(1) + "s · " + m.kind;
      const select = document.createElement("button");
      select.className = "secondary";
      select.textContent = "Select";
      select.addEventListener("click", () => {
        $("start").value = m.start;
        $("end").value = m.end;
        $("preview").currentTime = m.start;
        message("Selected " + m.start + "–" + m.end + "s. You can adjust the start and end.");
      });
      card.append(text, select);
      parent.appendChild(card);
    }
    message("Ready. Select a candidate or enter your own timestamps.");
  } catch (error) { message(error.message, true); } finally { button.disabled = false; }
});
$("generate").addEventListener("click", async () => {
  if (!uploadedAsset) return message("Upload a video file first.", true);
  const button = $("generate");
  button.disabled = true;
  $("status").textContent = "Starting render…";
  try {
    const result = await post("/v1/renders", {
      asset_id: uploadedAsset,
      start: Number($("start").value),
      end: Number($("end").value),
      headline: $("headline").value.trim(),
      caption_script: $("caption").value.trim(),
      narration_script: $("narration").value.trim() || null,
      rights: $("rights").value,
      rights_evidence: $("evidence").value.trim(),
      permission_to_publish: $("permission").checked
    });
    message("Rendering your vertical Short. The page will check for completion.");
    for (let attempt = 0; attempt < 240; attempt++) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      const state = await json("/v1/renders/" + result.job_id);
      if (state.status === "error") throw new Error(state.detail);
      if (state.status !== "ready") {
        $("status").textContent = "Processing video…";
        continue;
      }
      const fileResponse = await request(state.download_url);
      const blob = await fileResponse.blob();
      if (exportedBlobUrl) URL.revokeObjectURL(exportedBlobUrl);
      exportedBlobUrl = URL.createObjectURL(blob);
      $("result").src = exportedBlobUrl;
      $("download").disabled = false;
      $("status").textContent = "MP4 ready · " + (blob.size / 1048576).toFixed(1) + " MB";
      message("Your clip is ready to review. AI-generated voice and captions do not eliminate footage rights requirements.");
      return;
    }
    throw new Error("The render is still processing. Check your server status and retry.");
  } catch (error) {
    message(error.message, true);
    $("status").textContent = "Render failed";
  } finally { button.disabled = false; }
});
$("download").addEventListener("click", () => {
  if (!exportedBlobUrl) return;
  const link = document.createElement("a");
  link.href = exportedBlobUrl;
  link.download = "AIOClips-Short.mp4";
  document.body.appendChild(link);
  link.click();
  link.remove();
});
