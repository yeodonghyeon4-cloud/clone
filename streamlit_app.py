"""
ZABATDA - AI 기반 유사 상품 검색 서비스
Streamlit Cloud 배포용 애플리케이션
"""

import streamlit as st
from PIL import Image
from io import BytesIO
import sys
import os

# backend 모듈 임포트를 위한 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from embedding_service import generate_embedding_from_bytes, get_model_info
from database import search_similar_products, get_product_count

# 페이지 설정
st.set_page_config(
    page_title="ZABATDA - 위조품 검색",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
    }
    .logo-text {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1a1a1a;
    }
    .ko-name {
        color: #333;
    }
    .en-name {
        color: #666;
        font-size: 1.5rem;
    }
    .slogan {
        color: #888;
        font-size: 1rem;
    }
    .highlight {
        color: #ff6b6b;
        font-weight: bold;
    }
    .product-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
    }
    .similarity-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
    }
    .price-text {
        font-size: 1.2rem;
        font-weight: bold;
        color: #e74c3c;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # 헤더
    st.markdown("""
    <div class="main-header">
        <span class="ko-name">자밧다</span>
        <span class="en-name">ZABATDA</span>
        <span class="slogan">- 위조품 판별, 최저가 탐색</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("# 제품 이미지로 유사 제품의 <span class='highlight'>최저가</span>를 찾아보고,", unsafe_allow_html=True)
    st.markdown("# <span class='highlight'>위조품</span>을 판별하세요.", unsafe_allow_html=True)

    st.markdown("""
    이미지를 업로드하면 1688, 타오바오, 알리익스프레스, Temu에서
    **유사한 제품**의 최저가를 찾아드립니다.
    """)

    st.divider()

    # 파일 업로드
    uploaded_file = st.file_uploader(
        "제품 이미지를 업로드하세요",
        type=['jpg', 'jpeg', 'png', 'webp'],
        help="JPG, PNG, WEBP 형식 지원 (최대 16MB)"
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        if uploaded_file is not None:
            # 이미지 미리보기
            image = Image.open(uploaded_file)
            st.image(image, caption="업로드된 이미지", use_container_width=True)

            # 파일 정보
            file_size = len(uploaded_file.getvalue()) / 1024
            st.caption(f"파일명: {uploaded_file.name}")
            st.caption(f"크기: {file_size:.1f} KB")

    with col2:
        if uploaded_file is not None:
            # 검색 옵션
            with st.expander("검색 옵션", expanded=False):
                limit = st.slider("검색 결과 수", min_value=1, max_value=20, value=5)
                min_similarity = st.slider("최소 유사도", min_value=0.0, max_value=1.0, value=0.0, step=0.05)

            # 검색 버튼
            if st.button("🔍 AI 유사 상품 검색 시작", type="primary", use_container_width=True):
                with st.spinner("유사 상품을 분석 중입니다... 잠시만 기다려주세요."):
                    try:
                        # 이미지 바이트 읽기
                        uploaded_file.seek(0)
                        image_bytes = uploaded_file.read()

                        # 임베딩 생성
                        embedding = generate_embedding_from_bytes(image_bytes)

                        # 유사 상품 검색
                        results = search_similar_products(
                            query_embedding=embedding,
                            limit=limit,
                            min_similarity=min_similarity
                        )

                        # 세션 상태에 결과 저장
                        st.session_state.search_results = results
                        st.session_state.search_completed = True

                    except Exception as e:
                        st.error(f"검색 중 오류가 발생했습니다: {str(e)}")

    # 검색 결과 표시
    if st.session_state.get('search_completed') and st.session_state.get('search_results') is not None:
        results = st.session_state.search_results

        st.divider()
        st.subheader(f"🎯 검색 결과 ({len(results)}개)")

        if len(results) == 0:
            st.info("유사한 상품을 찾지 못했습니다. 다른 이미지로 시도해보세요.")
        else:
            # 결과를 그리드로 표시
            cols = st.columns(min(len(results), 3))

            for idx, product in enumerate(results):
                with cols[idx % 3]:
                    with st.container():
                        # 상품 이미지
                        if product.get('image_url'):
                            st.image(product['image_url'], use_container_width=True)

                        # 유사도 배지
                        similarity_pct = product['similarity'] * 100
                        if similarity_pct >= 90:
                            st.success(f"🎯 유사도: {similarity_pct:.1f}%")
                        elif similarity_pct >= 70:
                            st.warning(f"✨ 유사도: {similarity_pct:.1f}%")
                        else:
                            st.info(f"📌 유사도: {similarity_pct:.1f}%")

                        # 상품 정보
                        st.markdown(f"**{product['name']}**")
                        st.caption(f"브랜드: {product['brand']}")
                        st.markdown(f"<span class='price-text'>₩{product['price']:,}</span>", unsafe_allow_html=True)

                        # 링크 버튼
                        if product.get('product_url'):
                            st.link_button("🛒 상품 보기", product['product_url'], use_container_width=True)

                        st.divider()


# 사이드바: 시스템 정보
with st.sidebar:
    st.header("ℹ️ 시스템 정보")

    try:
        product_count = get_product_count()
        model_info = get_model_info()

        st.metric("등록된 상품 수", f"{product_count:,}개")
        st.caption(f"모델: {model_info['model_name']}")
        st.caption(f"임베딩 차원: {model_info['embedding_dimensions']}")

        if model_info['loaded']:
            st.success("✅ 모델 로드됨")
        else:
            st.warning("⏳ 모델 로딩 대기중")

    except Exception as e:
        st.error(f"DB 연결 실패: {str(e)}")

    st.divider()
    st.caption("ZABATDA MVP v1.0")
    st.caption("AI-Powered Product Similarity Search")


if __name__ == "__main__":
    main()
