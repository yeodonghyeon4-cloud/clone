// ============================================================================
// ZABATDA MVP - Frontend JavaScript
// AI-Powered Product Similarity Search
// ============================================================================

// ============================================================================
// CONFIGURATION
// ============================================================================

const API_BASE_URL = 'http://localhost:5001';
const API_ENDPOINTS = {
  search: '/api/search',
  health: '/health',
  stats: '/api/stats'
};

const MAX_FILE_SIZE = 16 * 1024 * 1024; // 16MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png'];
const SEARCH_RESULTS_LIMIT = 5;

// Debug mode
const DEBUG = true;

// View mode state
let currentView = 'similarity'; // 'similarity' or 'price'
let currentResults = []; // Store current results for re-sorting

function log(...args) {
  if (DEBUG) console.log('[ZABATDA]', ...args);
}

function logError(...args) {
  if (DEBUG) console.error('[ZABATDA ERROR]', ...args);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Validate uploaded file
 * @param {File} file - File object to validate
 * @returns {Object} - { valid: boolean, error: string }
 */
function validateFile(file) {
  if (!file) {
    return { valid: false, error: '파일이 선택되지 않았습니다.' };
  }

  // Check file type
  if (!ALLOWED_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: '지원하지 않는 파일 형식입니다. JPG 또는 PNG 이미지를 업로드해주세요.'
    };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    const sizeMB = (MAX_FILE_SIZE / 1024 / 1024).toFixed(0);
    return {
      valid: false,
      error: `파일 크기가 너무 큽니다. ${sizeMB}MB 이하의 이미지를 업로드해주세요.`
    };
  }

  return { valid: true, error: null };
}

/**
 * Format price in Korean Won
 * @param {number} price - Price in KRW
 * @returns {string} - Formatted price
 */
function formatPrice(price) {
  return `₩${price.toLocaleString('ko-KR')}`;
}

/**
 * Get similarity tier based on score
 * @param {number} similarity - Similarity score (0-1)
 * @returns {string} - Tier: excellent, very-good, good, fair
 */
function getSimilarityTier(similarity) {
  if (similarity >= 0.95) return 'excellent';
  if (similarity >= 0.80) return 'very-good';
  if (similarity >= 0.70) return 'good';
  return 'fair';
}

/**
 * Get similarity label in Korean
 * @param {number} similarity - Similarity score (0-1)
 * @returns {string} - Korean label
 */
function getSimilarityLabel(similarity) {
  if (similarity >= 0.95) return '매우 유사';
  if (similarity >= 0.80) return '유사';
  if (similarity >= 0.70) return '보통';
  return '낮음';
}

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} - Formatted file size
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/**
 * Show error message to user
 * @param {string} message - Error message
 */
function showError(message) {
  alert(message);
  logError(message);
}

// ============================================================================
// UPLOAD PAGE FUNCTIONALITY
// ============================================================================

let selectedFile = null;

/**
 * Initialize upload page event handlers
 */
function initializeUploadHandlers() {
  log('Initializing upload page handlers');

  const dropArea = document.getElementById('dropArea');
  const imageUpload = document.getElementById('imageUpload');
  const searchButton = document.getElementById('searchButton');
  const imagePreview = document.getElementById('imagePreview');
  const previewImage = document.getElementById('previewImage');
  const removeImage = document.getElementById('removeImage');

  if (!dropArea || !imageUpload || !searchButton) {
    logError('Required DOM elements not found');
    return;
  }

  // File input change handler
  imageUpload.addEventListener('change', function(e) {
    const file = e.target.files[0];
    handleFileSelect(file);
  });

  // Drop area click - trigger file input
  dropArea.addEventListener('click', function(e) {
    if (!e.target.closest('#removeImage')) {
      imageUpload.click();
    }
  });

  // Drag and drop handlers
  dropArea.addEventListener('dragover', function(e) {
    e.preventDefault();
    e.stopPropagation();
    dropArea.classList.add('drag-over');
  });

  dropArea.addEventListener('dragleave', function(e) {
    e.preventDefault();
    e.stopPropagation();
    dropArea.classList.remove('drag-over');
  });

  dropArea.addEventListener('drop', function(e) {
    e.preventDefault();
    e.stopPropagation();
    dropArea.classList.remove('drag-over');

    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  });

  // Remove image button
  if (removeImage) {
    removeImage.addEventListener('click', function(e) {
      e.stopPropagation();
      clearFileSelection();
    });
  }

  // Search button click handler
  searchButton.addEventListener('click', function() {
    handleSearch();
  });

  log('Upload handlers initialized');
}

/**
 * Handle file selection
 * @param {File} file - Selected file
 */
function handleFileSelect(file) {
  log('File selected:', file?.name);

  const validation = validateFile(file);

  if (!validation.valid) {
    showError(validation.error);
    return;
  }

  selectedFile = file;
  displayFilePreview(file);
  enableSearchButton();
}

/**
 * Display file preview
 * @param {File} file - File to preview
 */
function displayFilePreview(file) {
  const imagePreview = document.getElementById('imagePreview');
  const previewImage = document.getElementById('previewImage');
  const fileName = document.getElementById('fileName');
  const fileSize = document.getElementById('fileSize');
  const dropArea = document.getElementById('dropArea');

  if (!imagePreview || !previewImage) {
    logError('Preview elements not found');
    return;
  }

  // Create FileReader to read image as data URL
  const reader = new FileReader();

  reader.onload = function(e) {
    previewImage.src = e.target.result;
    if (fileName) fileName.textContent = file.name;
    if (fileSize) fileSize.textContent = formatFileSize(file.size);

    // Hide drop area and show preview
    if (dropArea) {
      dropArea.classList.add('hidden');
    }
    imagePreview.classList.remove('hidden');
  };

  reader.readAsDataURL(file);
  log('Preview displayed for:', file.name);
}

/**
 * Clear file selection
 */
function clearFileSelection() {
  selectedFile = null;

  const imagePreview = document.getElementById('imagePreview');
  const previewImage = document.getElementById('previewImage');
  const imageUpload = document.getElementById('imageUpload');
  const dropArea = document.getElementById('dropArea');

  // Hide preview and show drop area
  if (imagePreview) imagePreview.classList.add('hidden');
  if (previewImage) previewImage.src = '';
  if (imageUpload) imageUpload.value = '';

  // Show drop area again
  if (dropArea) {
    dropArea.classList.remove('hidden');
    dropArea.style.borderColor = '';
  }

  disableSearchButton();
  log('File selection cleared');
}

/**
 * Enable search button
 */
function enableSearchButton() {
  const searchButton = document.getElementById('searchButton');
  if (searchButton) {
    searchButton.disabled = false;
    searchButton.classList.remove('disabled');
  }
}

/**
 * Disable search button
 */
function disableSearchButton() {
  const searchButton = document.getElementById('searchButton');
  if (searchButton) {
    searchButton.disabled = true;
    searchButton.classList.add('disabled');
  }
}

/**
 * Show loading overlay
 */
function showLoading() {
  const loadingOverlay = document.getElementById('loadingOverlay');
  if (loadingOverlay) {
    loadingOverlay.classList.remove('hidden');
  }
}

/**
 * Hide loading overlay
 */
function hideLoading() {
  const loadingOverlay = document.getElementById('loadingOverlay');
  if (loadingOverlay) {
    loadingOverlay.classList.add('hidden');
  }
}

/**
 * Handle search button click
 */
async function handleSearch() {
  log('Search initiated');

  if (!selectedFile) {
    showError('이미지를 먼저 업로드해주세요.');
    return;
  }

  // Show loading state
  showLoading();
  disableSearchButton();

  try {
    // Create FormData for multipart upload
    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('limit', SEARCH_RESULTS_LIMIT.toString());

    log('Sending API request to:', `${API_BASE_URL}${API_ENDPOINTS.search}`);

    // Send API request
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.search}`, {
      method: 'POST',
      body: formData
    });

    log('API response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `API 오류: ${response.status}`);
    }

    const data = await response.json();
    log('API response data:', data);

    if (data.status !== 'success' || !data.results) {
      throw new Error('유효하지 않은 응답 형식입니다.');
    }

    // Store results and uploaded image in sessionStorage
    await storeResultsAndNavigate(data.results, selectedFile);

  } catch (error) {
    logError('Search failed:', error);
    hideLoading();
    enableSearchButton();

    let errorMessage = '검색 중 오류가 발생했습니다.';

    if (error.message.includes('Failed to fetch')) {
      errorMessage = '서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인해주세요.';
    } else if (error.message) {
      errorMessage = error.message;
    }

    showError(errorMessage);
  }
}

/**
 * Store results in sessionStorage and navigate to results page
 * @param {Array} results - Search results
 * @param {File} imageFile - Uploaded image file
 */
async function storeResultsAndNavigate(results, imageFile) {
  log('Storing results and navigating...');

  // Store search results
  sessionStorage.setItem('searchResults', JSON.stringify(results));

  // Convert image to data URL for display on results page
  const reader = new FileReader();

  reader.onload = function(e) {
    sessionStorage.setItem('uploadedImage', e.target.result);
    log('Results stored, navigating to result.html');
    window.location.href = 'result.html';
  };

  reader.onerror = function() {
    logError('Failed to read image file');
    showError('이미지 처리 중 오류가 발생했습니다.');
    hideLoading();
    enableSearchButton();
  };

  reader.readAsDataURL(imageFile);
}

// ============================================================================
// RESULTS PAGE FUNCTIONALITY
// ============================================================================

/**
 * Initialize results page
 */
function initializeResultsPage() {
  log('Initializing results page');

  // Check if data exists
  const resultsData = sessionStorage.getItem('searchResults');
  const uploadedImage = sessionStorage.getItem('uploadedImage');

  if (!resultsData || !uploadedImage) {
    logError('No search data found, redirecting to index');
    alert('검색 결과가 없습니다. 다시 검색해주세요.');
    window.location.href = 'index.html';
    return;
  }

  try {
    const results = JSON.parse(resultsData);
    displayResults(results, uploadedImage);
  } catch (error) {
    logError('Failed to parse results:', error);
    alert('검색 결과를 불러오는 중 오류가 발생했습니다.');
    window.location.href = 'index.html';
  }
}

/**
 * Display search results
 * @param {Array} results - Search results
 * @param {string} uploadedImageUrl - Data URL of uploaded image
 */
function displayResults(results, uploadedImageUrl) {
  log('Displaying results:', results.length, 'products');

  // Store results globally for view switching
  currentResults = [...results];

  // Display uploaded image
  const searchedImage = document.getElementById('searchedImage');
  if (searchedImage) {
    searchedImage.innerHTML = `
      <img src="${uploadedImageUrl}" alt="검색한 이미지" style="width: 100%; border-radius: 8px;">
    `;
  }

  // Display result summary
  const resultSummary = document.getElementById('resultSummary');
  if (resultSummary) {
    const maxSimilarity = results.length > 0
      ? Math.max(...results.map(r => r.similarity))
      : 0;

    let summaryHTML = `<strong>${results.length}개의 유사 상품</strong>을 찾았습니다.`;

    if (results.length > 0) {
      summaryHTML += `<br>최고 유사도: ${(maxSimilarity * 100).toFixed(1)}%`;

      // Add guidance if similarity is low
      if (maxSimilarity < 0.7) {
        summaryHTML += `<br><span style="color: #ffc107;">💡 더 나은 결과를 위해 다른 각도의 이미지를 시도해보세요.</span>`;
      }
    }

    resultSummary.innerHTML = summaryHTML;
  }

  // Display result count badge
  const resultCount = document.getElementById('resultCount');
  if (resultCount) {
    resultCount.textContent = results.length;
  }

  // Render products based on current view
  renderProducts(results);

  log('Results displayed successfully');
}

/**
 * Render product cards based on current view mode
 * @param {Array} results - Products to render
 */
function renderProducts(results) {
  const resultsGrid = document.getElementById('resultsGrid');
  if (!resultsGrid) return;

  if (results.length === 0) {
    resultsGrid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 40px;">
        <p style="font-size: 18px; color: #5a6c7d;">유사한 제품을 찾지 못했습니다.</p>
        <p style="color: #999;">다른 이미지로 다시 시도해보세요.</p>
      </div>
    `;
  } else {
    resultsGrid.innerHTML = results.map((product, index) =>
      createProductCard(product, index)
    ).join('');
  }
}

/**
 * Switch between similarity and price view modes
 * @param {string} viewMode - 'similarity' or 'price'
 */
function switchView(viewMode) {
  log('Switching view to:', viewMode);

  currentView = viewMode;

  // Update button active states
  const similarityBtn = document.getElementById('sortBySimilarityBtn');
  const priceBtn = document.getElementById('sortByPriceBtn');

  if (similarityBtn && priceBtn) {
    if (viewMode === 'similarity') {
      similarityBtn.classList.add('active');
      priceBtn.classList.remove('active');
    } else {
      priceBtn.classList.add('active');
      similarityBtn.classList.remove('active');
    }
  }

  // Sort and re-render results
  let sortedResults;
  if (viewMode === 'price') {
    // Sort by price (ascending - cheapest first)
    sortedResults = [...currentResults].sort((a, b) => a.price - b.price);
  } else {
    // Sort by similarity (descending - best match first)
    sortedResults = [...currentResults].sort((a, b) => b.similarity - a.similarity);
  }

  renderProducts(sortedResults);
  log('View switched successfully to:', viewMode);
}

/**
 * Create product card HTML
 * @param {Object} product - Product data
 * @param {number} index - Product index (0-based)
 * @returns {string} - Product card HTML
 */
function createProductCard(product, index) {
  const similarityPercent = (product.similarity * 100).toFixed(1);
  const tier = getSimilarityTier(product.similarity);
  const label = getSimilarityLabel(product.similarity);

  // Rank badge for top 3
  let rankBadge = '';
  if (index === 0) {
    rankBadge = '<div class="rank-badge top-1">1위</div>';
  } else if (index === 1) {
    rankBadge = '<div class="rank-badge top-2">2위</div>';
  } else if (index === 2) {
    rankBadge = '<div class="rank-badge top-3">3위</div>';
  }

  return `
    <div class="product-card">
      ${rankBadge}
      <a href="${product.product_url}" target="_blank" rel="noopener noreferrer" class="product-image">
        <img src="${API_BASE_URL}${product.image_url}" alt="${product.name}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Crect fill=%22%23f0f0f0%22 width=%22200%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%23999%22%3ENo Image%3C/text%3E%3C/svg%3E'">
      </a>
      <div class="product-info">
        <h4 class="product-name">${product.name}</h4>

        <div class="similarity-section">
          <div class="similarity-score ${tier}">
            유사도: ${similarityPercent}%
          </div>
          <div class="similarity-bar">
            <div class="similarity-bar-fill ${tier}" style="width: ${similarityPercent}%"></div>
          </div>
          <span class="similarity-badge ${tier}">${label}</span>
        </div>

        <div class="product-meta">
          <div class="product-price">${formatPrice(product.price)}</div>
          <div class="product-brand">${product.brand || '브랜드 정보 없음'}</div>
        </div>
      </div>
    </div>
  `;
}

// ============================================================================
// PAGE INITIALIZATION
// ============================================================================

/**
 * Initialize app based on current page
 */
document.addEventListener('DOMContentLoaded', function() {
  log('DOM loaded, initializing app');

  // Detect current page
  const isResultsPage = window.location.pathname.includes('result.html');

  if (isResultsPage) {
    log('Results page detected');
    initializeResultsPage();
  } else {
    log('Upload page detected');
    initializeUploadHandlers();

    // Disable search button initially
    disableSearchButton();
  }
});

// ============================================================================
// EXPORT FOR TESTING (if needed)
// ============================================================================

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    validateFile,
    formatPrice,
    getSimilarityTier,
    getSimilarityLabel
  };
}
