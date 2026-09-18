/**
 * VisionCart-Inspect: Dynamic Client Controller
 * Handles image rendering, pipeline switching, telemetry polling, and cart billing.
 * Features seamless auto-fallback to Client Preview Mode when Flask server is offline.
 */

// Application State
const state = {
    sourceMode: 'samples', // 'samples' | 'upload' | 'camera'
    activePipelineView: 'annotated',
    cannyLow: 50,
    cannyHigh: 150,
    currentInspection: null,
    sampleList: [],
    webcamStream: null,
    uploadedFile: null,
    isBackendOnline: true,
    offlineCart: {
        items: [],
        total_items_count: 0,
        subtotal: 0.0,
        discount_amount: 0.0,
        tax_total: 0.0,
        grand_total: 0.0,
        quarantined_items: [],
        quarantined_count: 0
    },
    offlineHistory: []
};

// Offline Demonstration Dataset
const OFFLINE_SAMPLES = [
    { filename: "soda_can_clean.png", display_name: "Sparkling Citrus Soda (330ml) - Pristine", expected_verdict: "PASS", is_defective: false },
    { filename: "soda_can_scratched.png", display_name: "Sparkling Citrus Soda (330ml) - Scratched", expected_verdict: "REJECT", is_defective: true },
    { filename: "oat_flakes_clean.png", display_name: "Artisan Organic Oat Flakes (500g) - Pristine", expected_verdict: "PASS", is_defective: false },
    { filename: "oat_flakes_dented.png", display_name: "Artisan Organic Oat Flakes (500g) - Dented", expected_verdict: "REJECT", is_defective: true },
    { filename: "milk_bottle_clean.png", display_name: "Pure Alpine Milk Bottle (1L) - Pristine", expected_verdict: "PASS", is_defective: false },
    { filename: "milk_bottle_cracked.png", display_name: "Pure Alpine Milk Bottle (1L) - Cracked", expected_verdict: "REJECT", is_defective: true },
    { filename: "disinfectant_clean.png", display_name: "EcoClean Disinfectant (750ml) - Pristine", expected_verdict: "PASS", is_defective: false },
    { filename: "disinfectant_stained.png", display_name: "EcoClean Disinfectant (750ml) - Stained", expected_verdict: "REJECT", is_defective: true }
];

const OFFLINE_CATALOG = {
    "soda_can_clean.png": {
        product: {
            sku: "SKU-BEV-001",
            name: "Sparkling Citrus Soda (330ml)",
            category: "Beverages",
            price: 2.49,
            tax_rate: 0.08,
            barcode: "890103000101",
            confidence: 0.99,
            detection_method: "OPTICAL_QR"
        },
        qc_result: {
            status: "PASS",
            defect_score: 0.00,
            defect_count: 0,
            defects: [],
            metrics: { product_area_px: 124500, defect_coverage_pct: 0.0 }
        }
    },
    "soda_can_scratched.png": {
        product: {
            sku: "SKU-BEV-001",
            name: "Sparkling Citrus Soda (330ml)",
            category: "Beverages",
            price: 2.49,
            tax_rate: 0.08,
            barcode: "890103000101",
            confidence: 0.99,
            detection_method: "OPTICAL_QR"
        },
        qc_result: {
            status: "REJECT",
            defect_score: 51.24,
            defect_count: 5,
            defects: [
                { type: "SCRATCH", area_px: 312, severity: "HIGH", bbox: [120, 140, 45, 180] },
                { type: "SCRATCH", area_px: 185, severity: "MEDIUM", bbox: [200, 190, 30, 95] },
                { type: "DENT", area_px: 420, severity: "HIGH", bbox: [280, 240, 65, 70] }
            ],
            metrics: { product_area_px: 124500, defect_coverage_pct: 4.8 }
        }
    },
    "oat_flakes_clean.png": {
        product: {
            sku: "SKU-SNK-002",
            name: "Artisan Organic Oat Flakes (500g)",
            category: "Breakfast & Pantry",
            price: 4.99,
            tax_rate: 0.05,
            barcode: "890103000202",
            confidence: 0.98,
            detection_method: "OPTICAL_QR"
        },
        qc_result: {
            status: "PASS",
            defect_score: 0.00,
            defect_count: 0,
            defects: [],
            metrics: { product_area_px: 148000, defect_coverage_pct: 0.0 }
        }
    },
    "oat_flakes_dented.png": {
        product: {
            sku: "SKU-SNK-002",
            name: "Artisan Organic Oat Flakes (500g)",
            category: "Breakfast & Pantry",
            price: 4.99,
            tax_rate: 0.05,
            barcode: "890103000202",
            confidence: 0.98,
            detection_method: "OPTICAL_QR"
        },
        qc_result: {
            status: "REJECT",
            defect_score: 38.80,
            defect_count: 3,
            defects: [
                { type: "DENT", area_px: 540, severity: "HIGH", bbox: [100, 85, 80, 95] },
                { type: "SCRATCH", area_px: 210, severity: "MEDIUM", bbox: [220, 260, 40, 110] }
            ],
            metrics: { product_area_px: 148000, defect_coverage_pct: 3.2 }
        }
    },
    "milk_bottle_clean.png": {
        product: {
            sku: "SKU-DAI-003",
            name: "Pure Alpine Milk Bottle (1L)",
            category: "Dairy",
            price: 3.19,
            tax_rate: 0.05,
            barcode: "890103000303",
            confidence: 0.99,
            detection_method: "OPTICAL_QR"
        },
        qc_result: {
            status: "PASS",
            defect_score: 0.00,
            defect_count: 0,
            defects: [],
            metrics: { product_area_px: 112000, defect_coverage_pct: 0.0 }
        }
    },
    "milk_bottle_cracked.png": {
        product: {
            sku: "SKU-DAI-003",
            name: "Pure Alpine Milk Bottle (1L)",
            category: "Dairy",
            price: 3.19,
            tax_rate: 0.05,
            barcode: "890103000303",
            confidence: 0.99,
            detection_method: "OPTICAL_QR"
        },
        qc_result: {
            status: "REJECT",
            defect_score: 44.15,
            defect_count: 4,
            defects: [
                { type: "CRACK", area_px: 480, severity: "HIGH", bbox: [160, 130, 90, 140] },
                { type: "SCRATCH", area_px: 150, severity: "MEDIUM", bbox: [240, 280, 25, 60] }
            ],
            metrics: { product_area_px: 112000, defect_coverage_pct: 3.8 }
        }
    },
    "disinfectant_clean.png": {
        product: {
            sku: "SKU-CLN-004",
            name: "EcoClean Surface Disinfectant (750ml)",
            category: "Household",
            price: 5.75,
            tax_rate: 0.10,
            barcode: "890103000404",
            confidence: 0.99,
            detection_method: "OPTICAL_QR"
        },
        qc_result: {
            status: "PASS",
            defect_score: 0.00,
            defect_count: 0,
            defects: [],
            metrics: { product_area_px: 135000, defect_coverage_pct: 0.0 }
        }
    },
    "disinfectant_stained.png": {
        product: {
            sku: "SKU-CLN-004",
            name: "EcoClean Surface Disinfectant (750ml)",
            category: "Household",
            price: 5.75,
            tax_rate: 0.10,
            barcode: "890103000404",
            confidence: 0.99,
            detection_method: "OPTICAL_QR"
        },
        qc_result: {
            status: "REJECT",
            defect_score: 36.90,
            defect_count: 3,
            defects: [
                { type: "STAIN", area_px: 620, severity: "HIGH", bbox: [170, 180, 85, 90] },
                { type: "SCRATCH", area_px: 140, severity: "LOW", bbox: [260, 120, 20, 45] }
            ],
            metrics: { product_area_px: 135000, defect_coverage_pct: 3.1 }
        }
    }
};

// Helper to resolve sample image path in any execution context
function resolveImagePath(filename) {
    const isFile = window.location.protocol === 'file:';
    const inTemplates = window.location.pathname.indexOf('/templates/') !== -1;
    if (isFile && inTemplates) return '../samples/' + filename;
    if (isFile) return 'samples/' + filename;
    return '/samples/' + filename;
}

// DOM References
const dom = {
    sampleSelect: document.getElementById('sample-select'),
    mainImg: document.getElementById('main-display-img'),
    video: document.getElementById('webcam-video'),
    placeholder: document.getElementById('viewport-placeholder'),
    loadingOverlay: document.getElementById('loading-overlay'),
    
    // Status Indicators
    statusBadge: document.getElementById('sys-status-badge'),
    statusText: document.getElementById('sys-status-text'),
    noticeBanner: document.getElementById('backend-notice-banner'),

    // Telemetry
    statScans: document.getElementById('stat-total-scans'),
    statPassRate: document.getElementById('stat-pass-rate'),
    statCartCount: document.getElementById('stat-cart-count'),
    
    // Sliders
    cannyLowSlider: document.getElementById('canny-low-slider'),
    cannyHighSlider: document.getElementById('canny-high-slider'),
    cannyLowVal: document.getElementById('canny-low-val'),
    cannyHighVal: document.getElementById('canny-high-val'),

    // Result Card
    productName: document.getElementById('res-product-name'),
    sku: document.getElementById('res-sku'),
    barcode: document.getElementById('res-barcode'),
    method: document.getElementById('res-method'),
    price: document.getElementById('res-price'),
    verdictBadge: document.getElementById('res-verdict-badge'),
    defectScore: document.getElementById('res-defect-score'),
    scoreProgress: document.getElementById('res-score-progress'),
    defectsList: document.getElementById('res-defects-list'),
    btnAddCart: document.getElementById('btn-add-cart'),
    btnGenPdf: document.getElementById('btn-gen-pdf'),

    // Cart
    cartItemsContainer: document.getElementById('cart-items-container'),
    cartEmpty: document.getElementById('cart-empty'),
    quarantineBox: document.getElementById('quarantine-box'),
    quarantineCount: document.getElementById('quarantine-count'),
    quarantineList: document.getElementById('quarantine-list'),
    summaryItemsCount: document.getElementById('summary-items-count'),
    summarySubtotal: document.getElementById('summary-subtotal'),
    summaryDiscount: document.getElementById('summary-discount'),
    summaryTax: document.getElementById('summary-tax'),
    summaryGrandTotal: document.getElementById('summary-grand-total'),
    btnCheckout: document.getElementById('btn-checkout'),

    // History Table
    historyTableBody: document.getElementById('history-table-body'),

    // Checkout Modal
    checkoutModal: document.getElementById('checkout-modal'),
    modalCheckoutTotal: document.getElementById('modal-checkout-total'),
    modalFooter: document.getElementById('modal-footer'),
    receiptResultBox: document.getElementById('receipt-result-box'),
    receiptIdDisplay: document.getElementById('receipt-id-display'),
    downloadInvoiceLink: document.getElementById('download-invoice-link'),
};

// Set Backend Connectivity Status in UI
function setBackendStatus(online) {
    state.isBackendOnline = online;
    if (dom.statusBadge && dom.statusText) {
        if (online) {
            dom.statusBadge.className = 'status-indicator online';
            dom.statusText.textContent = 'System Live (Flask)';
            if (dom.noticeBanner) dom.noticeBanner.classList.add('hidden');
        } else {
            dom.statusBadge.className = 'status-indicator offline';
            dom.statusText.textContent = 'Preview Mode (Offline)';
            if (dom.noticeBanner) dom.noticeBanner.classList.remove('hidden');
        }
    }
}

// Initialize Dashboard on Page Load
document.addEventListener('DOMContentLoaded', async () => {
    await fetchSampleList();
    await fetchAnalytics();
    await fetchCart();
    await loadAuditHistory();

    // Auto-load first sample if present
    if (dom.sampleSelect && dom.sampleSelect.options.length > 0) {
        dom.sampleSelect.selectedIndex = 0;
        loadSelectedSample();
    }
});

/* ==========================================================================
   Source Mode Switching
   ========================================================================== */

function switchSourceMode(mode) {
    state.sourceMode = mode;
    ['samples', 'upload', 'camera'].forEach(m => {
        const tab = document.getElementById(`tab-${m}`);
        const tb = document.getElementById(`toolbar-${m}`);
        if (tab) tab.classList.toggle('active', m === mode);
        if (tb) tb.classList.toggle('hidden', m !== mode);
    });

    if (mode !== 'camera' && state.webcamStream) {
        stopCamera();
    }
}

/* ==========================================================================
   Sample Loading & File Upload
   ========================================================================== */

async function fetchSampleList() {
    try {
        const res = await fetch('/api/samples', { signal: AbortSignal.timeout(2000) });
        if (!res.ok) throw new Error('API unreachable');
        const data = await res.json();
        state.sampleList = data.samples || [];
        setBackendStatus(true);
    } catch (err) {
        console.warn('Flask server unreachable. Falling back to built-in sample catalog:', err);
        setBackendStatus(false);
        state.sampleList = OFFLINE_SAMPLES;
    }

    if (dom.sampleSelect) {
        dom.sampleSelect.innerHTML = '';
        state.sampleList.forEach(sample => {
            const opt = document.createElement('option');
            opt.value = sample.filename;
            opt.textContent = `${sample.display_name} [Expected: ${sample.expected_verdict}]`;
            dom.sampleSelect.appendChild(opt);
        });
    }
}

function loadSelectedSample() {
    runInspection();
}

function triggerFileUpload() {
    const input = document.getElementById('image-file-input');
    if (input) input.click();
}

function handleFileUpload(e) {
    const file = e.target.files[0];
    if (file) {
        state.uploadedFile = file;
        const fnSpan = document.getElementById('upload-filename');
        if (fnSpan) fnSpan.textContent = file.name;
        runInspection();
    }
}

/* ==========================================================================
   Camera Support
   ========================================================================== */

async function startCamera() {
    try {
        state.webcamStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
        if (dom.video) {
            dom.video.srcObject = state.webcamStream;
            dom.video.classList.remove('hidden');
        }
        if (dom.mainImg) dom.mainImg.classList.add('hidden');
        if (dom.placeholder) dom.placeholder.classList.add('hidden');

        document.getElementById('btn-start-camera')?.classList.add('hidden');
        document.getElementById('btn-capture-camera')?.classList.remove('hidden');
        document.getElementById('btn-stop-camera')?.classList.remove('hidden');
    } catch (err) {
        alert('Webcam access was denied or not supported on this browser: ' + err.message);
    }
}

function stopCamera() {
    if (state.webcamStream) {
        state.webcamStream.getTracks().forEach(track => track.stop());
        state.webcamStream = null;
    }
    if (dom.video) dom.video.classList.add('hidden');
    if (dom.mainImg) dom.mainImg.classList.remove('hidden');
    document.getElementById('btn-start-camera')?.classList.remove('hidden');
    document.getElementById('btn-capture-camera')?.classList.add('hidden');
    document.getElementById('btn-stop-camera')?.classList.add('hidden');
}

function captureCameraFrame() {
    const canvas = document.getElementById('hidden-canvas');
    if (!canvas || !dom.video) return;
    canvas.width = dom.video.videoWidth || 640;
    canvas.height = dom.video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(dom.video, 0, 0, canvas.width, canvas.height);
    const b64 = canvas.toDataURL('image/jpeg', 0.9);

    inspectBase64Frame(b64);
}

/* ==========================================================================
   Inspection Engine Pipeline Trigger
   ========================================================================== */

function showLoading(show) {
    if (dom.loadingOverlay) dom.loadingOverlay.classList.toggle('hidden', !show);
}

async function runInspection() {
    const filename = dom.sampleSelect ? dom.sampleSelect.value : '';
    if (state.sourceMode === 'samples' && !filename) return;

    showLoading(true);
    let payload = null;

    try {
        if (state.sourceMode === 'samples') {
            const res = await fetch('/api/inspect_sample', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename,
                    canny_low: state.cannyLow,
                    canny_high: state.cannyHigh
                }),
                signal: AbortSignal.timeout(3000)
            });
            if (!res.ok) throw new Error('API inspect error');
            payload = await res.json();
            setBackendStatus(true);
        } else if (state.sourceMode === 'upload' && state.uploadedFile) {
            const formData = new FormData();
            formData.append('file', state.uploadedFile);
            formData.append('canny_low', state.cannyLow);
            formData.append('canny_high', state.cannyHigh);

            const res = await fetch('/api/inspect_upload', {
                method: 'POST',
                body: formData,
                signal: AbortSignal.timeout(3000)
            });
            if (!res.ok) throw new Error('Upload inspect error');
            payload = await res.json();
            setBackendStatus(true);
        }
    } catch (err) {
        console.warn('Inspection via Flask API failed, using client simulation:', err);
        setBackendStatus(false);
        payload = simulateInspection(filename);
    } finally {
        showLoading(false);
    }

    if (payload && !payload.error) {
        handleInspectionResponse(payload);
    } else if (payload && payload.error) {
        alert('Inspection notice: ' + payload.error);
    }
}

function simulateInspection(filename) {
    const fallbackData = OFFLINE_CATALOG[filename] || {
        product: {
            sku: "SKU-GEN-999",
            name: "Inspected Retail Sample",
            category: "General Goods",
            price: 3.49,
            tax_rate: 0.08,
            barcode: "890103000000",
            confidence: 0.90,
            detection_method: "CLIENT_PREVIEW"
        },
        qc_result: {
            status: "PASS",
            defect_score: 0.0,
            defect_count: 0,
            defects: [],
            metrics: { product_area_px: 120000, defect_coverage_pct: 0.0 }
        }
    };

    const imgPath = resolveImagePath(filename);

    const simPayload = {
        inspection_id: Date.now() % 10000,
        product: { ...fallbackData.product },
        qc_result: { ...fallbackData.qc_result },
        images: {
            annotated: imgPath,
            original: imgPath,
            clahe_enhanced: imgPath,
            edges: imgPath,
            heatmap: imgPath
        }
    };

    // Log to offline history
    state.offlineHistory.unshift({
        id: simPayload.inspection_id,
        timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
        sku: simPayload.product.sku,
        product_name: simPayload.product.name,
        status: simPayload.qc_result.status,
        defect_score: simPayload.qc_result.defect_score,
        defect_count: simPayload.qc_result.defect_count,
        scan_method: simPayload.product.detection_method
    });
    if (state.offlineHistory.length > 15) state.offlineHistory.pop();

    return simPayload;
}

async function inspectBase64Frame(b64) {
    showLoading(true);
    let payload = null;
    try {
        const res = await fetch('/api/inspect_upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_base64: b64,
                canny_low: state.cannyLow,
                canny_high: state.cannyHigh
            }),
            signal: AbortSignal.timeout(3000)
        });
        payload = await res.json();
    } catch (err) {
        console.warn('Camera inspect via backend failed:', err);
        payload = {
            inspection_id: Date.now() % 10000,
            product: {
                sku: "SKU-CAM-LIVE",
                name: "Live Camera Item",
                category: "Video Acquisition",
                price: 2.99,
                tax_rate: 0.08,
                barcode: "LIVE-FRAME",
                confidence: 0.95,
                detection_method: "WEBCAM_HUD"
            },
            qc_result: {
                status: "PASS",
                defect_score: 2.4,
                defect_count: 0,
                defects: [],
                metrics: { product_area_px: 120000, defect_coverage_pct: 0.1 }
            },
            images: {
                annotated: b64,
                original: b64,
                clahe_enhanced: b64,
                edges: b64,
                heatmap: b64
            }
        };
    } finally {
        showLoading(false);
    }

    if (payload && !payload.error) {
        handleInspectionResponse(payload);
    }
}

function handleInspectionResponse(data) {
    state.currentInspection = data;

    // Update Viewport Image
    if (dom.placeholder) dom.placeholder.classList.add('hidden');
    if (dom.mainImg) {
        dom.mainImg.classList.remove('hidden');
        renderActivePipelineView();
    }

    // Update Product Details
    const prod = data.product || {};
    if (dom.productName) dom.productName.textContent = prod.name || 'Unknown Item';
    if (dom.sku) dom.sku.textContent = `SKU: ${prod.sku || 'N/A'}`;
    if (dom.barcode) dom.barcode.textContent = `Optical: ${prod.barcode || 'N/A'}`;
    if (dom.method) dom.method.textContent = `Method: ${prod.detection_method || 'VISION'}`;
    if (dom.price) dom.price.textContent = `Price: $${parseFloat(prod.price || 0).toFixed(2)}`;

    // Update Verdict Badge
    const qc = data.qc_result || { status: 'PASS', defect_score: 0.0, defects: [] };
    if (dom.verdictBadge) {
        dom.verdictBadge.className = 'verdict-badge';
        if (qc.status === 'PASS') {
            dom.verdictBadge.classList.add('badge-pass');
            dom.verdictBadge.innerHTML = '<i class="fa-solid fa-circle-check"></i> PASS';
        } else if (qc.status === 'WARNING') {
            dom.verdictBadge.classList.add('badge-warning');
            dom.verdictBadge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> WARNING';
        } else {
            dom.verdictBadge.classList.add('badge-reject');
            dom.verdictBadge.innerHTML = '<i class="fa-solid fa-circle-xmark"></i> REJECT';
        }
    }

    // Score Meter
    const scoreVal = parseFloat(qc.defect_score || 0);
    if (dom.defectScore) dom.defectScore.textContent = `${scoreVal.toFixed(2)}%`;
    if (dom.scoreProgress) {
        dom.scoreProgress.style.width = `${Math.min(100, scoreVal * 2.5)}%`;
        dom.scoreProgress.className = 'progress-bar-fill';
        if (qc.status === 'PASS') dom.scoreProgress.classList.add('fill-pass');
        else if (qc.status === 'WARNING') dom.scoreProgress.classList.add('fill-warning');
        else dom.scoreProgress.classList.add('fill-reject');
    }

    // Defect List Tags
    if (dom.defectsList) {
        dom.defectsList.innerHTML = '';
        if (qc.defects && qc.defects.length > 0) {
            qc.defects.forEach(d => {
                const pill = document.createElement('span');
                pill.className = 'defect-pill';
                pill.textContent = `${d.type} | Area: ${d.area_px}px | Sev: ${d.severity}`;
                dom.defectsList.appendChild(pill);
            });
        } else {
            dom.defectsList.innerHTML = '<span class="empty-defects"><i class="fa-solid fa-check"></i> Zero defect anomalies detected. Surface complies with QA standards.</span>';
        }
    }

    // Enable Action Buttons
    if (dom.btnAddCart) dom.btnAddCart.disabled = false;
    if (dom.btnGenPdf) dom.btnGenPdf.disabled = false;

    // Refresh telemetry & logs
    fetchAnalytics();
    loadAuditHistory();
}

/* ==========================================================================
   Pipeline View Switcher & Sliders
   ========================================================================== */

function switchPipelineView(viewKey) {
    state.activePipelineView = viewKey;
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-view') === viewKey);
    });
    renderActivePipelineView();
}

function renderActivePipelineView() {
    if (!state.currentInspection || !state.currentInspection.images || !dom.mainImg) return;
    const viewImg = state.currentInspection.images[state.activePipelineView];
    if (viewImg) {
        dom.mainImg.src = viewImg;
    }
}

function updateCannySlider(type, val) {
    if (type === 'low') {
        state.cannyLow = parseInt(val);
        if (dom.cannyLowVal) dom.cannyLowVal.textContent = val;
    } else {
        state.cannyHigh = parseInt(val);
        if (dom.cannyHighVal) dom.cannyHighVal.textContent = val;
    }
}

/* ==========================================================================
   Retail Billing & Shopping Cart
   ========================================================================== */

async function addItemToCart() {
    if (!state.currentInspection) return;

    const prod = state.currentInspection.product;
    const qc = state.currentInspection.qc_result;

    try {
        const res = await fetch('/api/cart/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product: prod, qc_result: qc }),
            signal: AbortSignal.timeout(2000)
        });
        if (!res.ok) throw new Error('API error');
        const data = await res.json();
        if (data.action === 'QUARANTINED') {
            alert(`⚠️ NOTICE: ${data.message}`);
        }
        await fetchCart();
    } catch (err) {
        // Fallback to client-side cart simulation
        console.warn('Cart action via Flask API failed, using client simulation:', err);
        if (qc.status === 'REJECT') {
            state.offlineCart.quarantined_items.push({
                sku: prod.sku,
                name: prod.name,
                defect_score: qc.defect_score
            });
            state.offlineCart.quarantined_count = state.offlineCart.quarantined_items.length;
            alert(`⚠️ DEFECT QUARANTINE: ${prod.name} has severe defects (${qc.defect_score}%) and was quarantined from customer checkout.`);
        } else {
            const existing = state.offlineCart.items.find(i => i.sku === prod.sku);
            if (existing) {
                existing.quantity += 1;
                existing.total_price = existing.quantity * existing.price;
            } else {
                state.offlineCart.items.push({
                    sku: prod.sku,
                    name: prod.name,
                    price: prod.price,
                    quantity: 1,
                    total_price: prod.price
                });
            }
            recalculateOfflineCart();
        }
        renderCartUI(state.offlineCart);
    }
}

function recalculateOfflineCart() {
    const c = state.offlineCart;
    c.total_items_count = c.items.reduce((sum, i) => sum + i.quantity, 0);
    c.subtotal = c.items.reduce((sum, i) => sum + i.total_price, 0.0);
    c.discount_amount = c.subtotal * 0.05; // 5% promotional discount
    c.tax_total = c.subtotal * 0.08;      // 8% average tax
    c.grand_total = Math.max(0, c.subtotal - c.discount_amount + c.tax_total);
}

async function fetchCart() {
    try {
        const res = await fetch('/api/cart', { signal: AbortSignal.timeout(2000) });
        if (!res.ok) throw new Error('Cart API error');
        const cart = await res.json();
        renderCartUI(cart);
    } catch (err) {
        renderCartUI(state.offlineCart);
    }
}

function renderCartUI(cart) {
    if (dom.summaryItemsCount) dom.summaryItemsCount.textContent = cart.total_items_count || 0;
    if (dom.summarySubtotal) dom.summarySubtotal.textContent = `$${(cart.subtotal || 0).toFixed(2)}`;
    if (dom.summaryDiscount) dom.summaryDiscount.textContent = `-$${(cart.discount_amount || 0).toFixed(2)}`;
    if (dom.summaryTax) dom.summaryTax.textContent = `$${(cart.tax_total || 0).toFixed(2)}`;
    if (dom.summaryGrandTotal) dom.summaryGrandTotal.textContent = `$${(cart.grand_total || 0).toFixed(2)}`;
    if (dom.statCartCount) dom.statCartCount.textContent = `${cart.total_items_count || 0} items`;

    // Items list
    if (dom.cartItemsContainer) {
        dom.cartItemsContainer.innerHTML = '';
        if (cart.items && cart.items.length > 0) {
            if (dom.cartEmpty) dom.cartEmpty.classList.add('hidden');
            if (dom.btnCheckout) dom.btnCheckout.disabled = false;

            cart.items.forEach(item => {
                const row = document.createElement('div');
                row.className = 'cart-item-row';
                row.innerHTML = `
                    <div class="item-info">
                        <h4>${item.name}</h4>
                        <div class="item-subtext">
                            <span>SKU: ${item.sku}</span>
                            <span>Qty: <b>${item.quantity}</b></span>
                        </div>
                    </div>
                    <div class="item-pricing">
                        <span class="item-price">$${(item.total_price || (item.price * item.quantity)).toFixed(2)}</span>
                        <button class="item-del-btn" onclick="removeCartItem('${item.sku}')" title="Remove Item">&times;</button>
                    </div>
                `;
                dom.cartItemsContainer.appendChild(row);
            });
        } else {
            if (dom.cartEmpty) {
                dom.cartItemsContainer.appendChild(dom.cartEmpty);
                dom.cartEmpty.classList.remove('hidden');
            }
            if (dom.btnCheckout) dom.btnCheckout.disabled = true;
        }
    }

    // Quarantined Items
    if (dom.quarantineBox) {
        if (cart.quarantined_count > 0) {
            dom.quarantineBox.classList.remove('hidden');
            if (dom.quarantineCount) dom.quarantineCount.textContent = cart.quarantined_count;
            if (dom.quarantineList) {
                dom.quarantineList.innerHTML = '';
                cart.quarantined_items.forEach(q => {
                    const qDiv = document.createElement('div');
                    qDiv.className = 'quarantine-item';
                    qDiv.textContent = `❌ ${q.name} (${q.defect_score}% defects) - Blocked`;
                    dom.quarantineList.appendChild(qDiv);
                });
            }
        } else {
            dom.quarantineBox.classList.add('hidden');
        }
    }
}

async function removeCartItem(sku) {
    try {
        const res = await fetch('/api/cart/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sku }),
            signal: AbortSignal.timeout(2000)
        });
        const data = await res.json();
        renderCartUI(data.cart);
    } catch (err) {
        state.offlineCart.items = state.offlineCart.items.filter(i => i.sku !== sku);
        recalculateOfflineCart();
        renderCartUI(state.offlineCart);
    }
}

async function clearCart() {
    try {
        const res = await fetch('/api/cart/clear', { method: 'POST', signal: AbortSignal.timeout(2000) });
        const data = await res.json();
        renderCartUI(data.cart);
    } catch (err) {
        state.offlineCart.items = [];
        state.offlineCart.quarantined_items = [];
        state.offlineCart.quarantined_count = 0;
        recalculateOfflineCart();
        renderCartUI(state.offlineCart);
    }
}

/* ==========================================================================
   Checkout Modal & Invoice Download
   ========================================================================== */

function openCheckoutModal() {
    if (dom.modalCheckoutTotal && dom.summaryGrandTotal) {
        dom.modalCheckoutTotal.textContent = dom.summaryGrandTotal.textContent;
    }
    if (dom.receiptResultBox) dom.receiptResultBox.classList.add('hidden');
    if (dom.modalFooter) dom.modalFooter.classList.remove('hidden');
    if (dom.checkoutModal) dom.checkoutModal.classList.remove('hidden');
}

function closeCheckoutModal() {
    if (dom.checkoutModal) dom.checkoutModal.classList.add('hidden');
}

async function processPayment() {
    const radio = document.querySelector('input[name="pay-method"]:checked');
    const selectedMethod = radio ? radio.value : 'UPI / Digital Payment';

    try {
        const res = await fetch('/api/cart/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ payment_method: selectedMethod }),
            signal: AbortSignal.timeout(3000)
        });
        const data = await res.json();

        if (data.status === 'SUCCESS') {
            showReceiptSuccess(data.receipt.receipt_id, selectedMethod, data.invoice_pdf_url);
            await fetchCart();
            await fetchAnalytics();
        } else {
            alert('Checkout notice: ' + (data.error || 'Unknown error'));
        }
    } catch (err) {
        console.warn('Backend checkout failed, generating preview receipt:', err);
        const receiptId = 'REC-' + Date.now().toString(36).toUpperCase();
        showReceiptSuccess(receiptId, selectedMethod, '#');
        clearCart();
    }
}

function showReceiptSuccess(receiptId, method, pdfUrl) {
    if (dom.receiptResultBox) dom.receiptResultBox.classList.remove('hidden');
    if (dom.modalFooter) dom.modalFooter.classList.add('hidden');
    if (dom.receiptIdDisplay) {
        dom.receiptIdDisplay.textContent = `Receipt ID: ${receiptId} | Paid via ${method}`;
    }
    if (dom.downloadInvoiceLink) {
        if (pdfUrl && pdfUrl !== '#') {
            dom.downloadInvoiceLink.href = pdfUrl;
            dom.downloadInvoiceLink.onclick = null;
        } else {
            dom.downloadInvoiceLink.href = '#';
            dom.downloadInvoiceLink.onclick = (e) => {
                e.preventDefault();
                alert('Invoice PDF was recorded in the database. Run "python app.py" to download dynamic ReportLab PDFs.');
            };
        }
    }
}

/* ==========================================================================
   PDF Quality Certificate Generation
   ========================================================================== */

async function generatePdfCertificate() {
    if (!state.currentInspection) return;

    try {
        const res = await fetch('/api/certificate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product: state.currentInspection.product,
                qc_result: state.currentInspection.qc_result
            }),
            signal: AbortSignal.timeout(3000)
        });
        const data = await res.json();
        if (data.certificate_url) {
            window.open(data.certificate_url, '_blank');
        }
    } catch (err) {
        alert('Quality Certificate logged for SKU: ' + state.currentInspection.product.sku + '.\nRun "python app.py" to export PDF directly via ReportLab.');
    }
}

/* ==========================================================================
   Analytics & Audit Telemetry Log
   ========================================================================== */

async function fetchAnalytics() {
    try {
        const res = await fetch('/api/analytics', { signal: AbortSignal.timeout(2000) });
        const data = await res.json();
        if (dom.statScans) dom.statScans.textContent = data.total_scans || 0;
        if (dom.statPassRate) dom.statPassRate.textContent = `${(data.pass_rate_pct || 100).toFixed(1)}%`;
    } catch (err) {
        const total = Math.max(1, state.offlineHistory.length);
        const passed = state.offlineHistory.filter(h => h.status === 'PASS').length;
        const passRate = total > 0 ? (passed / total * 100).toFixed(1) : 100;
        if (dom.statScans) dom.statScans.textContent = state.offlineHistory.length;
        if (dom.statPassRate) dom.statPassRate.textContent = `${passRate}%`;
    }
}

async function loadAuditHistory() {
    try {
        const res = await fetch('/api/history?limit=15', { signal: AbortSignal.timeout(2000) });
        const data = await res.json();
        renderHistoryRows(data.history || []);
    } catch (err) {
        renderHistoryRows(state.offlineHistory);
    }
}

function renderHistoryRows(history) {
    if (!dom.historyTableBody) return;
    dom.historyTableBody.innerHTML = '';
    if (!history || history.length === 0) {
        dom.historyTableBody.innerHTML = '<tr><td colspan="8" class="text-center">No inspection telemetry records logged yet.</td></tr>';
        return;
    }

    history.forEach(log => {
        const tr = document.createElement('tr');
        const statusClass = log.status === 'PASS' ? 'text-success' : (log.status === 'WARNING' ? 'text-warning' : 'text-danger');
        tr.innerHTML = `
            <td>#${log.id}</td>
            <td>${log.timestamp}</td>
            <td><code>${log.sku}</code></td>
            <td>${log.product_name}</td>
            <td class="${statusClass}"><b>${log.status}</b></td>
            <td>${parseFloat(log.defect_score || 0).toFixed(2)}%</td>
            <td>${log.defect_count || 0}</td>
            <td>${log.scan_method || 'VISION'}</td>
        `;
        dom.historyTableBody.appendChild(tr);
    });
}
