document.addEventListener('DOMContentLoaded', () => {
  const solidRadio = document.getElementById('colorModeSolid');
  const gradientRadio = document.getElementById('colorModeGradient');
  const solidOptions = document.getElementById('solidColorOptions');
  const gradientOptions = document.getElementById('gradientOptions');

  solidRadio.addEventListener('change', () => {
    if (solidRadio.checked) {
      solidOptions.style.display = 'block';
      gradientOptions.style.display = 'none';
    }
  });

  gradientRadio.addEventListener('change', () => {
    if (gradientRadio.checked) {
      solidOptions.style.display = 'none';
      gradientOptions.style.display = 'block';
    }
  });

  // Initial preview update
  updatePreview();
});

// Function to update live preview
function updatePreview() {
  const url = document.getElementById('url').value || 'https://example.com';
  const backColor = document.getElementById('backColor').value;
  const colorMode = document.querySelector('input[name="colorMode"]:checked').value;
  let fillColor = '#000000';

  if (colorMode === 'solid') {
    fillColor = document.getElementById('fillColor').value;
  } else {
    // For gradient, use first color for simplicity in preview
    fillColor = document.getElementById('gradientColor1').value;
  }

  const previewContainer = document.getElementById('qrcode'); // Changed from 'preview' to 'qrcode'
  previewContainer.innerHTML = '<p class="text-muted">Generating preview...</p>';

  // Use qrcode library to generate preview
  new QRCode(previewContainer, {
    text: url,
    width: 200,
    height: 200,
    colorDark: fillColor,
    colorLight: backColor,
  });
}

// Add event listeners for real-time updates
document.getElementById('url').addEventListener('input', updatePreview);
document.getElementById('backColor').addEventListener('input', updatePreview);
document.getElementById('colorModeSolid').addEventListener('change', updatePreview);
document.getElementById('colorModeGradient').addEventListener('change', updatePreview);
document.getElementById('fillColor').addEventListener('input', updatePreview);
document.getElementById('gradientColor1').addEventListener('input', updatePreview);

async function generateQRCode() {
  const url = document.getElementById('url').value;
  const backColor = document.getElementById('backColor').value;
  const logoFile = document.getElementById('logo').files[0];
  const moduleShape = document.getElementById('moduleShape').value;
  const colorMode = document.querySelector('input[name="colorMode"]:checked').value;

  if (!url) {
    alert('Enter a URL');
    return;
  }

  let payload = {
    url,
    backColor,
    moduleShape,
    colorMode,
    logo: null
  };

  if (colorMode === 'solid') {
    payload.fillColor = document.getElementById('fillColor').value;
  } else {
    payload.gradientType = document.getElementById('gradientType').value;
    payload.gradientColor1 = document.getElementById('gradientColor1').value;
    payload.gradientColor2 = document.getElementById('gradientColor2').value;
  }

  if (logoFile) {
    payload.logo = await new Promise((res, rej) => {
      const reader = new FileReader();
      reader.onload = e => res(e.target.result);
      reader.onerror = rej;
      reader.readAsDataURL(logoFile);
    });
  }

  try {
      const resp = await fetch('/api/qrcode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!resp.ok) {
        const errorData = await resp.json().catch(() => ({ error: 'Server error generating QR' }));
        alert(`Error: ${errorData.error || 'Unknown server error'}`);
        return;
      }

      const { image } = await resp.json();
      displayQRCode(image);
  } catch (error) {
      console.error('Fetch error:', error);
      alert('Failed to connect to the server.');
  }
}

function displayQRCode(dataUrl) {
  const container = document.getElementById('qrcode'); // Changed from 'preview' to 'qrcode'
  container.innerHTML = '';
  const img = new Image();
  img.src = dataUrl;
  img.alt = 'Generated QR Code';
  img.style.maxWidth = '100%';
  img.style.height = 'auto';
  img.style.borderRadius = '10px';
  container.appendChild(img);

  let dlButton = container.querySelector('.download-button');
  if (!dlButton) {
      dlButton = document.createElement('button');
      dlButton.textContent = 'Download QR Code';
      dlButton.className = 'btn btn-secondary mt-3 download-button';
      dlButton.onclick = () => {
        const a = document.createElement('a');
        a.href = dataUrl;
        a.download = 'qr_code.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      };
      container.appendChild(dlButton);
  } else {
      dlButton.onclick = () => {
        const a = document.createElement('a');
        a.href = dataUrl;
        a.download = 'qr_code.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      };
  }
}
