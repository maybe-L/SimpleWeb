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
            let lastMenuNumber = document.querySelectorAll('.menu-item').length;
            let nextMenuNumber = lastMenuNumber + 1;

            // 새로운 메뉴 항목을 추가할 div 생성
            const menuDiv = document.createElement("div");
            menuDiv.classList.add("menu-item");
            menuDiv.setAttribute("id", `menu-item-${nextMenuNumber}`);

            menuDiv.innerHTML = `
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
                <label for="menu_order_${nextMenuNumber}">Order:</label>
                <input type="number" name="menu_order_${nextMenuNumber}" value="${nextMenuNumber}" class="small-input">
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
            const menuIndex = e.target.getAttribute('data-index');
            const menuItem = document.getElementById(`menu-item-${menuIndex}`);
            if (menuItem) {
                menuItem.remove();  // 해당 메뉴 삭제
                console.log(`Menu ${menuIndex} removed`);
            } else {
                console.error(`Menu item with id menu-item-${menuIndex} not found`);
            }
        }
    });

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
