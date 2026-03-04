const isLocal = window.location.port === "5500" || window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

const API_BASE_URL = isLocal 
    ? "http://127.0.0.1:8000"  // 내 컴퓨터에서 작업할 때
    : "http://223.130.143.55:8000";  // 서버