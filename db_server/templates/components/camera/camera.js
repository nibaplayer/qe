
// 使用 JavaScript 发起 Ajax 请求
function loadCameraContent() {
  var xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function() {
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 200) {
        // 更新相应的 <div> 内容
        document.getElementById('camera_container').innerHTML = xhr.responseText;
      } else {
        console.error('Failed to load camera content.');
      }
    }
  };
  xhr.open('GET', '/getCameraFrame', true);
  xhr.send();
}

// 页面加载完成后调用加载函数
window.onload = function() {
  loadCameraContent();
};
