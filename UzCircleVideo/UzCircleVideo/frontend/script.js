// Replace BACKEND_URL with your Render service URL, e.g. https://uzcirclevideo.onrender.com
const BACKEND_URL = ""; // <-- SET THIS before deploy (or after you have Render URL)

const fileInput = document.getElementById('file');
const sendBtn = document.getElementById('sendBtn');
const status = document.getElementById('status');
const preview = document.getElementById('preview');
const previewWrap = document.getElementById('previewWrap');
const resultWrap = document.getElementById('resultWrap');
const downloadLink = document.getElementById('downloadLink');
const downloadP = document.getElementById('downloadP');
const progressBox = document.getElementById('progressBox');
const bar = document.getElementById('bar');
const ptext = document.getElementById('ptext');

let selectedFile = null;

fileInput.addEventListener('change', () => {
  const f = fileInput.files[0];
  if (!f) return;
  selectedFile = f;
  const tmp = URL.createObjectURL(f);
  preview.src = tmp;
  previewWrap.classList.remove('hidden');
  status.textContent = '✅ Fayl tanlandi. Tayyorlash uchun "Dumaloq shaklga keltirish" tugmasini bosing.';
  resultWrap.classList.add('hidden');
  downloadLink.classList.add('hidden');
});

function setProgress(p){
  const pct = Math.round(p*100);
  bar.style.width = pct + '%';
  ptext.textContent = pct + '%';
  progressBox.classList.remove('hidden');
}

sendBtn.addEventListener('click', async () => {
  if (!selectedFile) { alert('Avval video yuklang!'); return; }
  if (!BACKEND_URL) { alert('Backend URL script.js ichida BACKEND_URL ga o'rnatilmagan. Render URL ni qo'ying.'); return; }

  // reset UI
  resultWrap.classList.add('hidden');
  downloadLink.classList.add('hidden');
  setProgress(0);
  status.textContent = '⏳ Fayl serverga yuborilmoqda...';

  const fd = new FormData();
  fd.append('file', selectedFile);

  try {
    const resp = await fetch(BACKEND_URL + '/process', {
      method: 'POST',
      body: fd
    });

    if (!resp.ok) {
      const err = await resp.json().catch(()=>({error:'server error'}));
      status.textContent = '❌ Xatolik: ' + (err.error || 'Server error');
      return;
    }

    status.textContent = '⏳ Server ishlayapti, faylni olish uchun kuting...';
    // get blob
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    downloadLink.href = url;
    downloadLink.classList.remove('hidden');
    downloadLink.download = 'uzcircle_720p.webm';
    downloadP.textContent = '✅ Tayyor! Quyidagi tugma bilan yuklab oling:';
    resultWrap.classList.remove('hidden');
    status.textContent = '✅ Tayyor!';
    progressBox.classList.add('hidden');
  } catch (err) {
    console.error(err);
    status.textContent = '❌ Xato: ' + err.message;
  }
});
