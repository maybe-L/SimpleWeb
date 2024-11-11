console.log('script.js is running');

document.addEventListener('DOMContentLoaded', function () {
    console.log('DOMContentLoaded event fired');  // DOM 로드 확인

    const setupForm = document.getElementById('setup-form');
    const checkUrlButton = document.getElementById('check-url-button');
    const checkEmailButton = document.getElementById('check-email-button');
    const addMenuButton = document.getElementById('addMenuButton');
    let existingMenus = document.querySelectorAll('.menu-item');
    let nextMenuNumber = existingMenus.length + 1;
    
    // 1. URL 중복 확인 버튼 클릭 이벤트
    if (checkUrlButton) {
        checkUrlButton.addEventListener('click', checkUrlAvailability);
    } else {
        console.error('Check URL button not found!');
    }

    // 2. 이메일 중복 확인 버튼 클릭 이벤트
    if (checkEmailButton) {
        checkEmailButton.addEventListener('click', function() {
            console.log('Check Availability button clicked');
            const email = document.getElementById('email').value;
            const messageElement = document.getElementById('email-message');

            fetch(`/check_email?email=${encodeURIComponent(email)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.exists) {
                        messageElement.textContent = data.message;
                        messageElement.style.color = 'red';
                        messageElement.style.display = 'block';
                    } else {
                        messageElement.textContent = data.message;
                        messageElement.style.color = 'green';
                        messageElement.style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('Error checking email:', error);
                    messageElement.textContent = 'Error occurred. Please try again later.';
                    messageElement.style.color = 'red';
                    messageElement.style.display = 'block';
                });
        });
    } else {
        console.error('Check Email button not found!');
    }

    // 3. 폼 제출 시 유효성 검사
    if (setupForm) {
        setupForm.addEventListener('submit', function (event) {
            const warningMessage = document.getElementById('submission-warning');
            const websiteName = document.getElementById('website-name').value;
            const menuItems = document.querySelectorAll('.menu-item');
            let valid = true;

            // URL 중복 확인 여부 체크
            if (!urlChecked && !document.getElementById('website-url').hasAttribute('readonly')) {
                warningMessage.textContent = "Please check URL availability before submitting.";
                warningMessage.style.display = "block";
                valid = false;
            }

            // 웹사이트 이름이 비어있는지 확인
            if (!websiteName) {
                document.getElementById('website-name-message').style.display = "block";
                valid = false;
            } else {
                document.getElementById('website-name-message').style.display = "none";
            }

            // 각 메뉴 이름과 순서가 비어있는지 확인
            menuItems.forEach(function (menuItem, index) {
                const menuName = menuItem.querySelector(`input[name^="menu_name_"]`).value;
                const menuOrder = menuItem.querySelector(`input[name^="menu_order_"]`).value;
                const menuNameMessage = menuItem.querySelector('.menu-name-message');

                if (!menuName) {
                    menuNameMessage.style.display = "block";
                    valid = false;
                } else {
                    menuNameMessage.style.display = "none";
                }

                if (!menuOrder || isNaN(menuOrder)) {
                    console.log(`Order is invalid for menu ${index + 1}`);
                    valid = false;
                }
            });

            // 유효하지 않으면 폼 제출을 중단
            if (!valid) {
                event.preventDefault();
                console.log('Form validation failed.');
            } else {
                console.log('Form is valid, submitting.');
            }
        });
    } else {
        console.error('Setup form not found!');
    }

    // 4. 메뉴 추가 버튼 클릭 이벤트
    if (addMenuButton) {
        addMenuButton.addEventListener('click', function() {
            console.log('Add Menu button clicked');

            const menuContainer = document.getElementById('new-menu-container');
            const lastMenuOrder = document.querySelectorAll('.menu-item').length; // 마지막 메뉴의 오더 가져오기
            const nextMenuNumber = lastMenuOrder + 1;


            // 수평선 추가
            const hr = document.createElement('hr');
            menuContainer.appendChild(hr);


            // 새로운 메뉴 항목을 추가할 div 생성
            const menuDiv = document.createElement("div");
            menuDiv.classList.add("menu-item");
            menuDiv.setAttribute("id", `menu-item-${nextMenuNumber}`);

            menuDiv.innerHTML = `
                <label for="menu_order_${nextMenuNumber}">Order:</label>
                <input type="number" name="menu_order_${nextMenuNumber}" value="${nextMenuNumber}" class="small-input">
                <br>
                <label for="menu_name_${nextMenuNumber}">Menu ${nextMenuNumber} Name:</label>
                <input type="text" name="menu_name_${nextMenuNumber}" class="small-input" placeholder="Enter menu ${nextMenuNumber} name">
                <br>
                <label for="menu_type_${nextMenuNumber}">Menu ${nextMenuNumber} Type:</label>
                <select name="menu_type_${nextMenuNumber}" class="small-input">
                    <option value="home">Home</option>
                    <option value="list">List</option>
                    <option value="gallery">Gallery</option>
                </select>
                <br>
                <button type="button" class="delete-menu-button" data-index="${nextMenuNumber}">Delete Menu</button>
            `;


            // 메뉴 컨테이너에 새 메뉴 div 추가
            menuContainer.appendChild(menuDiv);
            nextMenuNumber++;

            console.log(`Menu ${nextMenuNumber} added`);
        });
    } else {
        console.error('Add Menu button not found!');
    }

    

// 5. 이벤트 위임 방식으로 삭제 버튼 처리
document.addEventListener('click', function(e) {
    if (e.target && e.target.classList.contains('delete-menu-button')) {
        console.log('Delete Menu button clicked');
        
        // 삭제할 메뉴 인덱스를 가져옴
        const menuIndex = e.target.getAttribute('data-index');
        const menuItem = document.getElementById(`menu-item-${menuIndex}`);
        
        if (menuItem) {
            // 메뉴 아이템의 이전 형제 요소가 수평선인지 확인 (이전 요소를 가져옴)
            const previousElement = menuItem.previousElementSibling;
            
            // 이전 형제가 수평선(hr)이면 삭제
            if (previousElement && previousElement.tagName === 'HR') {
                previousElement.remove();
                console.log('HR element removed');
            }
            
            // 메뉴 아이템 삭제
            menuItem.remove();  
            console.log(`Menu ${menuIndex} removed`);
            
            // 메뉴 삭제 후 인덱스 재정렬
            reindexMenus();
        } else {
            console.error(`Menu item with id menu-item-${menuIndex} not found`);
        }
    }
});

// 메뉴 삭제 후 남은 메뉴들의 인덱스 재정렬 함수
function reindexMenus() {
    const menuItems = document.querySelectorAll('.menu-item');
    
    // 모든 메뉴를 다시 순서대로 인덱스 재정렬
    menuItems.forEach((menuItem, index) => {
        const newIndex = index + 1; // 인덱스는 1부터 시작
        menuItem.id = `menu-item-${newIndex}`; // 새로운 id 설정
        
        // 메뉴 이름 필드의 인덱스 업데이트
        const menuNameLabel = menuItem.querySelector(`label[for^="menu_name_"]`);
        const menuNameInput = menuItem.querySelector(`input[name^="menu_name_"]`);
        if (menuNameLabel && menuNameInput) {
            menuNameLabel.setAttribute('for', `menu_name_${newIndex}`);
            menuNameLabel.innerText = `Menu ${newIndex} Name:`;
            menuNameInput.name = `menu_name_${newIndex}`;
        }

        // 메뉴 타입 필드의 인덱스 업데이트
        const menuTypeLabel = menuItem.querySelector(`label[for^="menu_type_"]`);
        const menuTypeSelect = menuItem.querySelector(`select[name^="menu_type_"]`);
        if (menuTypeLabel && menuTypeSelect) {
            menuTypeLabel.setAttribute('for', `menu_type_${newIndex}`);
            menuTypeSelect.name = `menu_type_${newIndex}`;
        }

        // 메뉴 오더 필드의 인덱스 업데이트
        const menuOrderLabel = menuItem.querySelector(`label[for^="menu_order_"]`);
        const menuOrderInput = menuItem.querySelector(`input[name^="menu_order_"]`);
        if (menuOrderLabel && menuOrderInput) {
            menuOrderLabel.setAttribute('for', `menu_order_${newIndex}`);
            menuOrderInput.name = `menu_order_${newIndex}`;
            menuOrderInput.value = newIndex; // 순서를 다시 설정
        }

        // 삭제 버튼의 인덱스 업데이트
        const deleteButton = menuItem.querySelector('.delete-menu-button');
        if (deleteButton) {
            deleteButton.setAttribute('data-index', newIndex);
        }
    });

    console.log('Menu indices reindexed');
}




    // 6. 햄버거 메뉴 토글
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            const rect = hamburger.getBoundingClientRect();
            navMenu.style.top = `${rect.bottom}px`;
            navMenu.style.left = `${rect.left}px`;
            navMenu.classList.toggle('show');
            console.log('Show class toggled:', navMenu.classList.contains('show'));
        });
    }

    // 7. 어드민바 높이에 따라 헤더 위치 조정
    adjustHeaderMargin(); // 페이지 로드 시에 호출

    // 8. 브라우저 크기 변경 시 재조정
    window.addEventListener('resize', function () {
        adjustHeaderMargin(); // 브라우저 크기 변경 시에 호출
    });
});

// 어드민바 높이에 따라 헤더 위치 조정 함수
function adjustHeaderMargin() {
    const adminBar = document.getElementById('admin-bar');
    const header = document.querySelector('header');

    if (adminBar && header) {
        const adminBarHeight = adminBar.getBoundingClientRect().height;
        const adjustedHeight = adminBarHeight - 20;
        console.log('Admin bar height:', adminBarHeight);
        header.style.marginTop = adjustedHeight + 'px';
        console.log('Header margin-top applied:', header.style.marginTop);
    }
}

// URL 중복 확인 함수
function checkUrlAvailability() {
    const urlInput = document.getElementById('website-url').value;
    const messageElement = document.getElementById('url-message');
    const warningMessage = document.getElementById('submission-warning');

    fetch(`/check_url?website_url=${encodeURIComponent(urlInput)}`)
        .then(response => response.json())
        .then(data => {
            if (data.available) {
                messageElement.textContent = "This URL is available.";
                messageElement.style.color = "green";
                messageElement.style.display = "block";
                warningMessage.style.display = "none";
                urlChecked = true;
            } else {
                messageElement.textContent = "This URL is already taken. Please choose another one.";
                messageElement.style.color = "red";
                messageElement.style.display = "block";
                warningMessage.style.display = "none";
                urlChecked = false;
            }
        })
        .catch(error => {
            console.error('Error checking URL:', error);
            messageElement.textContent = "Error checking URL availability. Please try again.";
            messageElement.style.color = "red";
            messageElement.style.display = "block";
        });
}

document.addEventListener('DOMContentLoaded', function() {
    const saveButton = document.getElementById('save-button');

    if (saveButton) {
        saveButton.addEventListener('click', function(event) {
            event.preventDefault();
            console.log("Save button clicked");

            const captureElement = document.querySelector('#menu-content');  // 캡처 대상 요소 확인
            const menuName = saveButton.getAttribute('data-menu-name');  // HTML에서 데이터 속성으로 메뉴 이름 가져오기

            if (captureElement) {
                // 캡처 요소를 최상위로 설정
                const originalZIndex = captureElement.style.zIndex;
                captureElement.style.zIndex = "9999";
                
                // 캡처 위치로 스크롤 이동
                const originalScrollPosition = window.scrollY;
                window.scrollTo(0, captureElement.offsetTop);

                // 지연 시간 추가 후 캡처 시작
                setTimeout(() => {
                    html2canvas(captureElement, { useCORS: true }).then(function(canvas) {
                        console.log("Canvas captured successfully");

                        const dataUrl = canvas.toDataURL('image/jpeg');
                        console.log("Data URL generated for thumbnail:", dataUrl);

                        // 서버로 캡처된 이미지 전송
                        fetch('/upload-thumbnail', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                            },
                            body: JSON.stringify({
                                image: dataUrl,
                                menu_name: menuName  // 현재 페이지의 동적 메뉴 이름
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                console.log('Thumbnail saved successfully:', data);
                            } else {
                                console.error('Error saving thumbnail:', data.message);
                            }
                        })
                        .catch(error => {
                            console.error('Fetch request failed:', error);
                        });

                        // 캡처 완료 후 원래 위치와 스타일 복원
                        window.scrollTo(0, originalScrollPosition);
                        captureElement.style.zIndex = originalZIndex;
                    }).catch(function(error) {
                        console.error("html2canvas 캡처 오류:", error);
                    });
                }, 100);  // 100ms 지연
            } else {
                console.error('menu-content 요소가 페이지에 존재하지 않습니다.');
            }
        });
    } else {
        console.error("Save button not found on the page.");
    }
});
