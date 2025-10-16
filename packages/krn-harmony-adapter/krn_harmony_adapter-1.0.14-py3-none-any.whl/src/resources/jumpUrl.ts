import isString from 'lodash/isString';
import { NativeModules } from 'react-native';
import { localLifeUrlLogger } from '@locallife/log';
import { getAppProps } from '@locallife/init';
import { logException } from '@locallife/utils';
import { URL } from 'react-native-url-polyfill';

const jumpAfterLogin = (
    urlValue: string,
    descValue: string,
    exceptionCallback?: (e) => void,
) => {
    const appModel = getAppProps();
    if (
        urlValue.startsWith('kwailive') ||
        urlValue.startsWith('kwai://locallife/half')
    ) {
        let newUrl = urlValue;
        if (urlValue.startsWith('kwailive://krndialog')) {
            try {
                const url = new URL(urlValue);
                const jumpUrlParam = url.searchParams.get('jumpUrl');
                if (jumpUrlParam) {
                    newUrl = `${urlValue.replace(
                        'kwailive://krndialog',
                        'kwai://locallife/krndialog',
                    )}`;
                } else {
                    newUrl = `kwai://locallife/half?krn=${encodeURIComponent(
                        urlValue.replace('kwailive://krndialog', 'kwai://krn'),
                    )}`;
                }
            } catch (e) {}
        } else if (urlValue.startsWith('kwailive://webview')) {
            newUrl = urlValue.replace(
                'kwailive://webview',
                'kwai://locallife/half',
            );
        }
        NativeModules.Kds.invoke(
            'poi',
            'startRouter',
            JSON.stringify({
                url: newUrl,
            }),
        )
            .catch((e) => {
                exceptionCallback && exceptionCallback(e);
                logException('启动kwailive快链失败', JSON.stringify(e));
                descValue = descValue + '_jumpUrlError_' + JSON.stringify(e);
            })
            .finally(() => {
                localLifeUrlLogger.logUrl(newUrl, descValue);
            });
    } else if (urlValue.startsWith('kwaimerchant')) {
        NativeModules.Kds.invoke(
            'merchant',
            'startRouter',
            JSON.stringify({
                url: urlValue,
                rootTag: appModel?.rootTag,
            }),
        )
            .catch((e) => {
                exceptionCallback && exceptionCallback(e);
                logException('启动电商快链失败', JSON.stringify(e));
                descValue = descValue + '_jumpUrlError_' + JSON.stringify(e);
            })
            .finally(() => {
                localLifeUrlLogger.logUrl(urlValue, descValue);
            });
    } else {
        if (urlValue.startsWith('http')) {
            urlValue = 'kwai://yodaweb?url=' + encodeURIComponent(urlValue);
        }
        NativeModules.Kds.invoke(
            'platform',
            'loadUri',
            JSON.stringify({
                url: urlValue,
                rootTag: appModel?.rootTag,
            }),
        )
            .catch((e) => {
                exceptionCallback && exceptionCallback(e);
                logException('启动普通快链失败', JSON.stringify(e));
                descValue = descValue + '_jumpUrlError_' + JSON.stringify(e);
            })
            .finally(() => {
                localLifeUrlLogger.logUrl(urlValue, descValue);
            });
    }
};

function parseUrl(urlValue: string) {
    let urlParts = urlValue.split('?');
    let schemeAndPath = urlParts[0];
    let queryParams = urlParts.length > 1 ? urlParts[1] : '';

    let schemeParts = schemeAndPath.split('://');
    let scheme = schemeParts[0];
    let path = schemeParts.length > 1 ? schemeParts[1] : '';

    let queryParts = queryParams.split('&');
    let queryParameters: { [key: string]: string } = {};
    queryParts.forEach((part) => {
        let [key, value] = part.split('=');
        queryParameters[key] = decodeURIComponent(value);
    });

    return {
        scheme,
        path,
        queryParameters,
    };
}

/**
 * 打开某个快链（bottom_sheet半屏、h5、直播）
 * @param url 快链链接。必需参数
 * @param desc 快链描述用于标识快链唯一性，不要重复，必需参数
 * @param exceptionCallback 异常时的回调，可选参数
 * @returns
 */
export function jumpUrl(
    url: string,
    desc: string,
    exceptionCallback?: (e) => void,
) {
    let descValue = desc;
    let urlValue = url;
    if (isString(urlValue) && isString(descValue)) {
        const appModel = getAppProps();
        try {
            let { queryParameters } = parseUrl(urlValue);
            let needLogin = queryParameters.needLogin;
            if (needLogin === 'true' || needLogin === '1') {
                if (!NativeModules.KSUserInfo.getUserInfoSync().isLogin) {
                    NativeModules.Kds.invoke('social', 'login', null)
                        .then(() => {
                            // 发送js2js 通知
                            NativeModules.KrnBridge.publish(appModel?.rootTag, {
                                actionType: 'js2js',
                                action: 'KSLocalLifeUserLoginSuccess',
                            }).catch((error) => {
                                console.log(
                                    'jump login 发送js2js 通知失败',
                                    error,
                                );
                            });
                            jumpAfterLogin(
                                urlValue,
                                descValue,
                                exceptionCallback,
                            );
                        })
                        .catch((e) => {
                            exceptionCallback && exceptionCallback(e);
                            logException('登录失败', JSON.stringify(e));
                            descValue =
                                descValue + '_loginError_' + JSON.stringify(e);
                        })
                        .finally(() => {
                            localLifeUrlLogger.logUrl(urlValue, descValue);
                        });
                } else {
                    jumpAfterLogin(urlValue, descValue, exceptionCallback);
                }
            } else {
                jumpAfterLogin(urlValue, descValue, exceptionCallback);
            }
        } catch (error) {
            jumpAfterLogin(urlValue, descValue, exceptionCallback);
        }
    }
}

/**
 * 打开快链（bottom_sheet半屏、h5、直播）, 同时进行liveID的检查
 * @param url 快链链接。必需参数
 * @param currentLiveId 当前直播间的liveId
 * @param desc 快链描述用于标识快链唯一性，不要重复，必需参数
 * @param exceptionCallback 异常时的回调，可选参数
 * @returns
 */
export function jumpUrlWithCheckLiveId(
    url: string,
    currentLiveId: string,
    desc?: string,
    exceptionCallback?: (e) => void,
) {
    // const initData = getInitData() as IInitLiveAPPProps;
    // if (currentLiveId !== initData?.liveId) {
    //     bridgeInit({ ...initData, liveId: currentLiveId });
    // }
    try {
        jumpUrl(url || '', desc || '', exceptionCallback);
    } catch (e) {
        // NativeModules.Kds.invoke(
        //     'merchant',
        //     'startRouter',
        //     JSON.stringify({
        //         url: url || '',
        //         rootTag: initData?.rootTag || '',
        //     }),
        // ).catch((e) => {
        //     exceptionCallback && exceptionCallback(e);
        // });
    }
}
