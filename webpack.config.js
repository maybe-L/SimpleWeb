const path = require('path');

module.exports = {
    entry: './src/index.js', // 메인 JS 파일 경로
    output: {
        filename: 'bundle.js', // 번들된 파일명
        path: path.resolve(__dirname, 'app/static'), // 번들된 파일이 저장될 폴더
    },
    resolve: {
        alias: {
            '@ckeditor': path.resolve(__dirname, 'node_modules/@ckeditor') // CKEditor 모듈 경로 통일
        }
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-env'] // Babel 트랜스파일러 설정
                    }
                }
            },
            {
                test: /\.svg$/, // SVG 파일을 처리하기 위한 규칙
                use: 'file-loader',
            },
            {
                test: /\.css$/, // CSS 파일을 처리하기 위한 규칙
                use: ['style-loader', 'css-loader'], // CSS 파일을 번들에 포함시키기 위한 로더들
            }
        ]
    },
    mode: 'development', // 개발 모드로 설정
};
