1、修改package.json中的依赖库版本：

- react-native版本为：npm:@kds/react-native@0.62.2-ks.18-lixuan-harmony.9
- @kds/react-native-linear-gradient版本为：2.6.4

2、升级KRN CLI

2.1 全局升级（之前没适配过的强烈推荐直接使用全局的）

yarn global add @krn/cli

2.2 本地升级（适合于之前已经适配过的，package.json 中 @krn/cli 版本为类似 0.18.4-harmony.5 的）

yarn add -D @krn/cli

3、修改babel.config.js，在 alias 中配置组件包名替换

```js
module.exports = {
    presets: ['module:metro-react-native-babel-preset'],
    plugins: [
        [
            'module-resolver',
            {
                alias: {
                  	'react-native-linear-gradient':
                        '@kds/react-native-linear-gradient',
                    'react-native-gesture-handler':
                        '@kds/react-native-gesture-handler',
                    'react-native-tab-view': '@kds/react-native-tab-view',
                },
            },
        ]
}
```

4、在 package.json 中的 resolution 中锁定组件版本为鸿蒙适配版本

- "@kds/react-native-gesture-handler": "1.7.17-2-oh-SNAPSHOT",
- "@kds/react-native-sound": "0.11.8",
- "@kds/react-native-blur": "3.6.7",
- "@kds/refresh-list": "4.0.8",
- "@kds/lottie-react-native": "4.0.37",
- "@kds/react-native-linear-gradient": "2.6.4"
- "@kds/react-native-tab-view": "^2.16.1-SNAPSHOT"

5、在 package.json 中添加 @locallife/auto-adapt-harmony 依赖，版本号0.0.1-alpha.6

6、在 babel.config.js 中添加以下代码

```js
module.exports = {
    presets: ['module:metro-react-native-babel-preset'],
		plugins: [
        [
            '@locallife/auto-adapt-harmony/src/plugin/bridge-replace-plugin.js',
            {
                notSupportBridges: {
                    invoke: [
                        'getShowingPendants',
                        'publishRubas',
                        'setRubasDimension',
                        'setRubasDimensionBatch',
                      	'subscribe',
                      	'unSubscribe'
                    ],
                    'LiveRnBridge.execute': [],
                },
            },
        ],
        ['@locallife/auto-adapt-harmony/src/plugin/error-delete-plugin.js'],
  
      	// 直播间场景需要增加以下内容
      	[
            '@locallife/auto-adapt-harmony/src/plugin/file-replace-plugin.js',
            {
                replacements: {
                    '@locallife/utils': {
                        jumpUrl: '/harmony/jumpUrl.ts',
                    },
                },
            },
        ],
  
      	// 解决图片包裹View导致的性能问题
      	['@locallife/auto-adapt-harmony/src/plugin/transform-kwaimage-children.js'],
    ]
}
```

在当前模块 src 平级的位置创建 harmony 目录，并在该目录中添加 ../harmony/jumpUrl.ts文件

7、代码中的 charset=UTF-8 要改为 charset=utf-8

8、package.json 中的 react-redux 版本如果大于 8.0.0，需要替换为 ^7.2.6
