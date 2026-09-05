const goalInput = document.querySelector("#goalInput");
const fileInput = document.querySelector("#fileInput");
const uploadCard = document.querySelector("#uploadCard");
const previewBlock = document.querySelector("#previewBlock");
const previewList = document.querySelector("#previewList");
const clearAllBtn = document.querySelector("#clearAllBtn");
const submitBtn = document.querySelector("#submitBtn");

const stageTitle = document.querySelector("#stageTitle");
const stageAction = document.querySelector("#stageAction");
const stageSceneCn = document.querySelector("#stageSceneCn");
const stageSceneEn = document.querySelector("#stageSceneEn");
const stageImgBox = document.querySelector("#stageImgBox");
const pageNum = document.querySelector("#pageNum");
const btnPrev = document.querySelector("#btnPrev");
const btnNext = document.querySelector("#btnNext");
const errorTip = document.querySelector("#errorTip");
const stageCard = document.querySelector("#stageCard");
const emptyHint = document.querySelector("#emptyHint");

let selectedFiles = [];
let stepList = [];
let currentStepIndex = 0;
const stepImageCache = {};

function updateSubmitState(){
    const hasGoal = goalInput.value.trim().length > 0;
    const hasFile = selectedFiles.length > 0;
    submitBtn.disabled = !(hasGoal && hasFile);
}

function renderPreview(){
    previewList.innerHTML = "";
    if(selectedFiles.length ===0){
        previewBlock.classList.add("hidden");
        return;
    }
    previewBlock.classList.remove("hidden");
    selectedFiles.forEach((file,idx)=>{
        const item = document.createElement("div");
        item.className = "preview-item";
        const img = document.createElement("img");
        img.src = URL.createObjectURL(file);
        const delBtn = document.createElement("button");
        delBtn.className = "remove-btn";
        delBtn.innerText = "×";
        delBtn.onclick = ()=>{
            selectedFiles.splice(idx,1);
            renderPreview();
            updateSubmitState();
        };
        item.appendChild(img);
        item.appendChild(delBtn);
        previewList.appendChild(item);
    })
    updateSubmitState();
}

fileInput.addEventListener("change",(e)=>{
    const arr = Array.from(e.target.files);
    selectedFiles.push(...arr);
    renderPreview();
    fileInput.value = "";
})

uploadCard.addEventListener("dragover",(e)=>{
    e.preventDefault();
    uploadCard.classList.add("drag-over");
})
uploadCard.addEventListener("dragleave",()=>{
    uploadCard.classList.remove("drag-over");
})
uploadCard.addEventListener("drop",(e)=>{
    e.preventDefault();
    uploadCard.classList.remove("drag-over");
    if(e.dataTransfer.files.length>0){
        selectedFiles.push(...Array.from(e.dataTransfer.files));
        renderPreview();
    }
})

clearAllBtn.addEventListener("click",()=>{
    selectedFiles = [];
    renderPreview();
})

goalInput.addEventListener("input", updateSubmitState);

function renderCurrentStage() {
    if (!stepList || stepList.length === 0) return;
    const s = stepList[currentStepIndex];
    const total = stepList.length;

    stageTitle.innerText = `第${currentStepIndex + 1}阶段 · 阶段${currentStepIndex + 1}`;
    stageAction.innerText = s.action ?? "";
    stageSceneCn.innerText = s.scene_cn ?? s.scene ?? "";
    stageSceneEn.innerText = s.scene_en ?? "";
    pageNum.innerText = `${currentStepIndex + 1} / ${total}`;

    btnPrev.disabled = currentStepIndex <= 0;
    btnNext.disabled = currentStepIndex >= total - 1;

    const cacheImg = stepImageCache[currentStepIndex];
    if (cacheImg && cacheImg !== "error") {
        stageImgBox.innerHTML = `<img src="${cacheImg}" class="stage-img">`;
    } else if (cacheImg === "error") {
        stageImgBox.innerHTML = `<div class="img-loading">❌配图生成失败</div>`;
    } else {
        stageImgBox.innerHTML = `<div class="img-loading">⏳等待生成配图</div>`;
        triggerImageGen(currentStepIndex);
    }
}

btnPrev?.addEventListener("click", () => {
    if (currentStepIndex > 0) {
        currentStepIndex--;
        renderCurrentStage();
    }
});

btnNext?.addEventListener("click", () => {
    if (currentStepIndex < stepList.length - 1) {
        currentStepIndex++;
        renderCurrentStage();
    }
});

async function handleApiResult(stepsData) {
    errorTip.style.display = "none";
    stageCard.classList.remove("hidden");
    emptyHint.style.display = "none";

    stepList = stepsData;
    currentStepIndex = 0;
    Object.keys(stepImageCache).forEach(k => delete stepImageCache[k]);
    renderCurrentStage();
}

async function triggerImageGen(idx) {
    const item = stepList[idx];
    const prompt = item.scene_en || item.scene_cn || item.scene;
    if (!prompt) return;

    try {
        const res = await fetch("/api/generate-image", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: prompt })
        });
        const data = await res.json();
        stepImageCache[idx] = data.image_url;
        if (idx === currentStepIndex) renderCurrentStage();
    } catch (err) {
        stepImageCache[idx] = "error";
        if (idx === currentStepIndex) renderCurrentStage();
    }
}

function showError(msg) {
    errorTip.style.display = "block";
    errorTip.innerText = `请求失败: ${msg}`;
}

submitBtn.addEventListener("click", async ()=>{
    submitBtn.disabled = true;
    errorTip.style.display = "none";
    const formData = new FormData();
    formData.append("goal", goalInput.value.trim());
    selectedFiles.forEach(f=>formData.append("files", f));

    try{
        const resp = await fetch("/api/multi-steps",{
            method:"POST",
            body: formData
        })
        if(!resp.ok) throw new Error("接口异常");
        const json = await resp.json();
        if(!json.steps || json.steps.length === 0){
            showError("没有返回改造步骤");
            return;
        }
        await handleApiResult(json.steps);
    }catch(err){
        showError(err.message);
    }finally{
        updateSubmitState();
    }
})
