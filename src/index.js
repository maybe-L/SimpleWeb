console.log('index.js is loaded successfully!');

import ClassicEditor from '@ckeditor/ckeditor5-build-classic';
import Bold from '@ckeditor/ckeditor5-basic-styles/src/bold';
import Italic from '@ckeditor/ckeditor5-basic-styles/src/italic';
import Font from '@ckeditor/ckeditor5-font/src/font';
import Image from '@ckeditor/ckeditor5-image/src/image';
import ImageToolbar from '@ckeditor/ckeditor5-image/src/imagetoolbar';
import MediaEmbed from '@ckeditor/ckeditor5-media-embed/src/mediaembed';
import SimpleUploadAdapter from '@ckeditor/ckeditor5-upload/src/adapters/simpleuploadadapter';

// CKEditor 인스턴스 생성
ClassicEditor
    .create(document.querySelector('#editor'), {
        plugins: [Bold, Italic, Font, Image, ImageToolbar, MediaEmbed, SimpleUploadAdapter],
        toolbar: ['bold', 'italic', 'fontFamily', 'imageUpload', 'mediaEmbed'],
        simpleUpload: {
            uploadUrl: '/upload-image'
        }
    })
    .then(editor => {
        console.log('Editor was initialized', editor);
    })
    .catch(error => {
        console.error('There was a problem initializing the editor.', error);
    });
