import re

from log_translate.data_struct import Log, Level
from log_translate.globals import remember_value
from log_translate.log_translator import SubTagTranslator, TagStrTranslator


class SecTagDemoTranslator(SubTagTranslator):
    def __init__(self):
        super().__init__("DFJ",
                         re.compile(r"(?P<tag>.*?) *:(?P<msg>.*)"),
                         [
                             TagStrTranslator({
                                 "sec_tag": self.new_tag
                             })
                         ])

    def new_tag(self, tag, msg):
        return Log(translated=msg)


class BluetoothTranslator(TagStrTranslator):
    def __init__(self):
        super().__init__({
            "BluetoothAdapter": bluetooth_adapter,
            "BluetoothGatt": bluetooth_gatt,
            "bluetooth": bluetooth,
            "bt_stack": bt_stack,
            "bt_btm": bt_btm,
            "bt_rfcomm": bt_rfcomm,
            "BluetoothBondStateMachine": bluetooth_pairing_action,
            "WS_BT_BluetoothPairingRequest": bluetooth_pairing_action,
            "BluetoothDevice": bluetooth_pairing_action,
            "vendor.qti.bluetooth.*?[btstateinfo|uart_logs|logger]": bluetoothError,
            "BluetoothQualityReportNativeInterface": BluetoothQualityReportNativeInterface,
            "ActivityTaskManager": bluetooth_pairing_dialog
        })


code_state = {
    "10": "系统蓝牙 已关闭",
    "12": "系统蓝牙 已打开",
    "OFF": "系统蓝牙 已关闭",
    "ON": "系统蓝牙 已打开"
}

ConfirmReqReply = {
    "0": "Command succeeded",
    "1": "Command started OK. ",
    "2": "Device busy with another command ",
    "3": "No resources to issue command",
    "4": "Request for 1 or more unsupported modes",
    "5": "Illegal parameter value  ",
    "6": "Device in wrong mode for request ",
    "7": "Unknown remote BD address",
    "8": "Device timeout",
    "9": "A bad value was received from HCI",
    "10": "Generic error ",
    "11": "Authorization failed",
    "12": "Device has been reset",
    "13": "request is stored in control block",
    "14": "state machine gets illegal command",
    "15": "delay the check on encryption",
    "16": "Bad SCO over HCI data length",
    "17": "security passed, no security set ",
    "18": "security failed",
    "19": "repeated attempts for LE security requests",
    "20": "Secure Connections Only Mode can't be supported",
    "21": "The device is restrict listed",
    "22": "Handle for Pin or Key Missing"
}


def bluetooth(msg):
    # 10-16 20:00:22.179906  6948  6999 W bluetooth: [acl.cc:1995] OnConnectFail: Connection failed classic remote:xx:xx:xx:xx:77:ae reason:PAGE_TIMEOUT(0x04)
    if "onnect" in msg and "failed" in msg and "reason" in msg:
        return Log(translated=msg, level=Level.e)
    return None


def bt_stack(msg):
    # 应用程序正在执行蓝牙设备或服务的发现操作，并传递了相应的 UUID
    # bt_stack: [VERBOSE2:bta_jv_act.cc(784)] bta_jv_start_discovery_cback: bta_jv_cb.uuid=a49eaa15-cb06-495c-9f4f-bb80a90cdf00
    # p_sdp_rec 表示一个指向 Service Discovery Protocol (SDP) 记录的指针，而 0x0 则表示该指针的值为 null,一个 null 的 SDP 记录指针可能表示在发现操作过程中发生了错误或异常情况，导致没有正确地获取或创建 SDP 记录
    # bt_stack: [VERBOSE2:bta_jv_act.cc(787)] bta_jv_start_discovery_cback: p_sdp_rec=0x0
    #  bt_stack: [ERROR:bta_jv_act.cc(1352)] bta_jv_rfcomm_connect: sec_id=0 is zero or BTM_SetSecurityLevel failed, remote_scn:5
    #  bt_stack: [ERROR:bta_jv_act.cc(1352)] RFCOMM_CreateConnectionWithSecurity: no resources
    if "bta_jv_rfcomm_connect: sec_id=0" in msg:
        # 在Bluetooth中，RFCOMM（封装在蓝牙上的串行端口协议）连接的加密通常
        # 通过蓝牙安全管理（Bluetooth Security Manager，SM）来实现。
        # 以下是一般的步骤，说明如何在RFCOMM连接中实现加密
        # 1 配对设备： 加密的第一步通常是在设备之间建立蓝牙配对。在配对过程中，设备之间会交换一些信息，例如配对码或者PIN码。成功的配对过程为后续的安全性设置奠定了基础。
        # 2 建立RFCOMM连接： 一旦设备之间成功配对，你可以通过RFCOMM建立连接。在建立连接的过程中，可以通过安全管理器（SM）来协商连接的安全性。
        # 3 设置连接的安全级别： 安全管理器（SM）使用安全级别（Security Level）来定义连接的安全性。安全级别包括不安全、需要认证但不加密、需要认证和加密等级别。
        #       你可以使用SM函数（比如BTM_SetSecurityLevel）来设置连接的安全级别。
        #                          BTM_SEC_NONE： 没有安全性。
        #                          BTM_SEC_IN_AUTHENTICATE： 需要认证但不需要加密。
        #                          BTM_SEC_IN_AUTHORIZE： 需要认证和加密。
        # 4 启用加密： 在建立RFCOMM连接后，可以通过SM启用加密。加密的启用通常是通过协商加密密钥并将其应用于连接数据的过程。这确保了在数据传输期间使用加密算法来保护数据的机密性
        # 5 处理密钥更新： 在一些情况下，为了保持安全性，可以周期性地更新加密密钥。这有助于降低窃听者攻击的风险。SM通常负责协商和更新加密密钥。
        # 蓝牙协议栈问题，因为无法分配Security ID（安全标识符）导致，SM通过BTM_SetSecurityLevel函数设置安全级别失败，导致无法为通道{}创建RFCOMM连接
        result = re.search("remote_scn:(\d+)", msg)
        # 当Security ID为0时，通常表示有一个问题或者错误。这可能是由于以下一些情况导致的
        return Log(
            translated=f">>>>>>>>>> 系统蓝牙问题,可能是因为蓝牙协议栈资源不足无法分配Security ID（安全标识符）导致无法为通道[ch={result.group(1)}]创建RFCOMM连接，建议重新关闭开启系统蓝牙再试试 <<<<<<<< ",
            level=Level.e)
    if "is zero or BTM_SetSecurityLevel failed" in msg:
        result = re.search("remote_scn:(\d+)", msg)
        return Log(
            translated=f">>>>>>>>>> 系统蓝牙问题,SM通过BTM_SetSecurityLevel函数设置安全级别失败，导致无法为通道[ch={result.group(1)}]创建RFCOMM连接，建议重新关闭开启系统蓝牙再试试 <<<<<<<< ",
            level=Level.e)
    if "RFCOMM_CreateConnectionWithSecurity: no resources" in msg:
        return Log(
            translated=">>>>>>>>>> 系统蓝牙问题,蓝牙协议栈资源不足SM无法设置连接的安全级别导致无法创建rfcomm连接，建议重新关闭开启系统蓝牙再试试 <<<<<<<< ",
            level=Level.e)
    if "on_le_disconnect Handle : 0x45, Reason : 19" in msg:
        return Log(translated=f">>>>>>>>>> 蓝牙层被对端断开：{msg} <<<<<<<< ", level=Level.e)
    if "on_le_disconnect Handle : 0x45, Reason" in msg:
        # bt_stack( 2480): on_le_disconnect Handle : 0x45, Reason : 19
        return Log(translated=f">>>>>>>>>> 蓝牙层被断开原因为{msg[-2:]} <<<<<<<< ", level=Level.e)
    if "gatt_rsp_timeout disconnecting" in msg:
        return Log(translated=msg, level=Level.e)
    return None


def bt_btm(msg):
    # bt_btm              com.android.bluetooth        I  BTM_ConfirmReqReply() State: WAIT_NUM_CONFIRM  Res: 0
    # bt_btm              com.android.bluetooth        I  BTM_ConfirmReqReply() State: WAIT_NUM_CONFIRM  Res: 11
    if "BTM_ConfirmReqReply() State: WAIT_NUM_CONFIRM" in msg:
        result = re.search(r"Res: (\d+)", msg)
        if result:
            state = ConfirmReqReply[result.group(1)]
            if state:
                return Log(translated=">>>>>>>>>> pin码配对 确认结果 %s  <<<<<<<< " % state, level=Level.i)
    if "LogMsg: btm_acl_disconnected" in msg:
        # bt_btm  : LogMsg: btm_acl_disconnected status=0 handle=512 reason=22
        return Log(translated=f">>> bt_btm：蓝牙底层已经断开连接:{msg} <<<", level=Level.e)
    return None


def bt_rfcomm(msg):
    # # 12-08 10:32:03.787197  4908  6180 W bt_rfcomm: RFCOMM_CreateConnection - no resources
    # # 12-08 10:32:03.787227  4908  6180 E bt_btif : bta_jv_rfcomm_connect, RFCOMM_CreateConnection failed
    ignore_case_msg = msg.lower()
    if "connection" in ignore_case_msg and "no resources" in ignore_case_msg:
        return Log(
            translated=f">>>>>>>>>> 系统蓝牙问题,蓝牙协议栈资源不足SM无法设置连接的安全级别导致无法创建rfcomm连接，建议重新关闭开启系统蓝牙再试试 <<<<<<<< ",
            level=Level.e)
    return None


def bluetooth_pairing_dialog(msg):
    # ActivityTaskManager: Displayed com.oplus.wirelesssettings/com.android.settings.bluetooth.BluetoothPairingDialog
    # port_rfc_closed: RFCOMM connection closed, index=3, state=2 reason=Closed[19], UUID=111F, bd_addr=ac:73:52:3f:5b:0a, is_server=1
    if "BluetoothPairingDialog" in msg:
        result = re.search("Displayed.*BluetoothPairingDialog", msg)
        if result:
            return Log(translated=" ---------------- 配对PIN码弹窗弹出 ----------------- ", level=Level.i)
    return None


# BluetoothBondStateMachine|WS_BT_BluetoothPairingRequestBluetoothBondStateMachine|WS_BT_BluetoothPairingRequest|BluetoothAdapter.*called by|BluetoothPairingDialog|BTM_ConfirmReqReply() State
def bluetooth_pairing_action(msg):
    # 开始配对
    # WS_BT_BluetoothPairingRequest: onReceive() action is android.bluetooth.device.action.PAIRING_REQUEST
    if "action.PAIRING_REQUEST" in msg:
        return Log(
            translated=f" >>>>>>>>>> 收到配对请求的广播: android.bluetooth.device.action.PAIRING_REQUEST <<<<<<<< ",
            level=Level.i)
    # PIN码
    # BluetoothBondStateMachine: sspRequestCallback: [B@4e743fe name: [B@1a3875f cod: 7936 pairingVariant 0 passkey: 211603
    if "passkey" in msg:
        result = re.search(r"(?<=passkey: ).*", msg)
        return Log(translated=f" >>>>>>>>>> 蓝牙连接认证请求 passkey: {result.group()} <<<<<<<< ", level=Level.i)
    # 取消配对
    # BluetoothBondStateMachine: Bond State Change Intent:E4:40:97:3C:EB:1C BOND_BONDED => BOND_NONE
    # 确定配对
    # BluetoothBondStateMachine: Bond State Change Intent:E4:40:97:3C:EB:1C BOND_BONDING => BOND_BONDED
    if "BOND_NONE => BOND_BONDING" in msg:
        # 未绑定到绑定中 请求绑定
        result = re.search(r"(?<=:).*?(?= )", msg)
        return Log(translated=f" >>>>>>>>>> 设备: {result.group()} 正请求绑定 <<<<<<<< ", level=Level.i)
    if "BOND_BONDED => BOND_NONE" in msg:
        result = re.search(r"(?<=:).*?(?= )", msg)
        return Log(translated=f" >>>>>>>>>> 设备: {result.group()} 被解除绑定 <<<<<<<< ", level=Level.i)
    if "BOND_BONDING => BOND_NONE" in msg:
        result = re.search(r"(?<=:).*?(?= )", msg)
        return Log(translated=f" >>>>>>>>>> 设备: {result.group()} 取消绑定 <<<<<<<< ", level=Level.i)
    if " => BOND_BONDED" in msg:
        result = re.search(r"(?<=:).*?(?= )", msg)
        return Log(translated=f" >>>>>>>>>> 设备: {result.group()} 绑定成功 <<<<<<<< ", level=Level.i)

        # com.oplus.wirelesssettings   D  Pairing dialog accepted
        # BluetoothDevice    setPairingConfirmation(): confirm: true, called by: com.oplus.wirelesssettings
        # BluetoothDevice     cancelBondProcess() for device 74:86:69:FE:6F:14 called by pid: 31290 tid: 32523
        # BluetoothDevice: setPairingConfirmation(): confirm: true, called by: com.oplus.wirelesssettings
        # ActivityTaskManager: Displayed com.oplus.wirelesssettings/com.android.settings.bluetooth.BluetoothPairingDialog
    if "Pairing dialog accepted" in msg:
        return Log(translated=" ----------------- 点击配对按钮,用户同意配对 ----------------- ", level=Level.i)
    if "Pairing dialog canceled" in msg:
        return Log(translated=" ----------------- 点击取消按钮,用户取消配对 ----------------- ", level=Level.i)
    if "setPairingConfirmation(): confirm: true" in msg:
        return Log(translated=" ----------------- 点击配对按钮,用户同意配对 ----------------- ", level=Level.i)
    if "cancelBondProcess() for device" in msg:
        return Log(translated=" ----------------- 点击取消按钮,用户取消配对 ----------------- ", level=Level.i)
    if "PAIRING_REQUEST" in msg:
        return Log(translated=" ----------------------- 设备请求配对 ----------------------- ", level=Level.i)
    return None


def bluetooth_adapter(msg):
    if "getState()" in msg:
        # BluetoothAdapter: 251847304: getState(). Returning TURNING_ON
        # BluetoothAdapter: 134396450: getState(). Returning ON
        # BluetoothAdapter: 251847304: getState(). Returning OFF
        result = re.search("(?<=Returning ).*", msg)
        # result = re.search("Returning (.*)", msg)
        # result.grop(1)
        if result:
            result_group = result.group()
            if result_group in code_state:
                state = code_state[result_group]
                if not remember_value("bluetooth_state", state):
                    return None
                return Log(translated=">>>>>>>>>>  %s  <<<<<<<< " % state, level=Level.w)
    #  BluetoothAdapter: disable(): called by: com.android.systemui
    #  BluetoothAdapter: enable(): called by: com.android.systemui
    if "disable(): called by" in msg:
        result = re.search("(?<=by: ).*", msg)
        return Log(translated=f">>>>>>>>>>  通过【{result.group()}】关闭系统蓝牙  <<<<<<<< ", level=Level.e)
    if "enable(): called by" in msg:
        result = re.search("(?<=by: ).*", msg)
        return Log(translated=f">>>>>>>>>>  通过【{result.group()}】打开系统蓝牙  <<<<<<<< ", level=Level.e)
    return None


# noinspection PyTypeChecker
def bluetooth_gatt(msg: object) -> object:
    # 	行 30: 08-05 15:16:32.334 10352 10596 D BluetoothGatt: connect() - device: 30:E7:BC:68:B3:1F, auto: false
    # 	行 31: 08-05 15:16:32.334 10352 10596 D BluetoothGatt: registerApp()
    # 	行 32: 08-05 15:16:32.334 10352 10596 D BluetoothGatt: registerApp() - UUID=f4571777-e0da-45cc-b829-bb1cdec8b87a
    # 	行 33: 08-05 15:16:32.336 10352 23202 D BluetoothGatt: onClientRegistered() - status=0 clientIf=8
    # 	行 36: 08-05 15:16:32.346 10352 23202 D BluetoothGatt: onClientConnectionState() - status=257 clientIf=8 device=30:E7:BC:68:B3:1F
    if "cancelOpen()" in msg:
        result = re.search("device: (.*)", msg)
        return Log(translated=f">>>>>>>>>>  gatt 手机主动断开连接 {result.group(1)} <<<<<<<< ", level=Level.i)
    if "close()" in msg:
        return Log(translated=">>>>>>>>>>  gatt 手机主动关闭连接  <<<<<<<< ", level=Level.i)
    if "connect()" in msg:
        # connect() - device: 34:47:9A:31:52:CF, auto: false, eattSupport: false
        result = re.search("device: (.*?),", msg)
        return Log(translated=f">>>>>>>>>>  gatt 发起设备连接 > {result.group(1)} <<<<<<<< ", level=Level.i)
    return None


def bluetoothError(tag, msg):
    # 07-09 08:50:07.121  1659  6605 D vendor.qti.bluetooth@1.1-uart_logs: DumpLogs: -->
    # 07-09 08:50:07.121  1659  6605 E vendor.qti.bluetooth@1.1-uart_logs: DumpLogs: Unable to open the Dir /sys/kernel/tracing/instances/hsuart err: Permission denied (13)
    # 07-09 08:50:07.121  1659  6605 D vendor.qti.bluetooth@1.1-logger: ReadSsrLevel crash dump value 1
    # 07-09 08:50:07.121  1659  6605 I vendor.qti.bluetooth@1.1-logger: ReadSsrLevel: ssr_level set to 3
    # 07-09 08:50:07.121  1659  6605 D vendor.qti.bluetooth@1.1-btstateinfo: DumpBtState: Dumping stats into /data/vendor/ssrdump/ramdump_bt_state_2023-07-09_08-50-07.log
    # 07-09 08:50:07.121  1659  6605 D vendor.qti.bluetooth@1.1-btstateinfo: BtPrimaryCrashReason:Rx Thread Stuck
    # 07-09 08:50:07.121  1659  6605 D vendor.qti.bluetooth@1.1-btstateinfo: BtSecondaryCrashReason:Default
    # 07-09 08:50:07.121  1659  6605 D vendor.qti.bluetooth@1.1-btstateinfo: BQR RIE Crash Code : 0x07
    # 07-09 08:50:07.121  1659  6605 D vendor.qti.bluetooth@1.1-btstateinfo: BQR RIE Crash String : Rx Thread Stuck
    # bluetooth\DCS\bt_fw_dump\压缩包内有蓝牙日志
    if re.search(r"DumpLogs|Dumping|crash", msg, re.IGNORECASE):  # 成员运算符和推导式
        return Log(translated="%s %s [系统蓝牙出问题了]" % (tag, msg), level=Level.e)
    return None


def BluetoothQualityReportNativeInterface(msg):
    # BluetoothQualityReportNativeInterface: BQR: {
    # BluetoothQualityReportNativeInterface:   mAddr: 68:85:A4:6E:F3:36, mLmpVer: 0x0B, mLmpSubVer: 0x2106, mManufacturerId: 0x000F, mName: OPPO Watch 4 Pro F336, mBluetoothClass: 7a0704,
    # BluetoothQualityReportNativeInterface:   BqrCommon: {
    # BluetoothQualityReportNativeInterface:     mQualityReportId: Approaching LSTO(0x02), mPacketType: TYPE_NULL(0x02), mConnectionHandle: 0x0033, mConnectionRole: 1(1), mTxPowerLevel: 17, mRssi: -57, mSnr: 0, mUnusedAfhChannelCount: 12,
    # BluetoothQualityReportNativeInterface:     mAfhSelectUnidealChannelCount: 0, mLsto: 8000, mPiconetClock: 0x03F2A5A7, mRetransmissionCount: 186, mNoRxCount: 96760, mNakCount: 263, mLastTxAckTimestamp: 0x0A437698, mFlowOffCount: 0,
    # BluetoothQualityReportNativeInterface:     mLastFlowOnTimestamp: 0x00000000, mOverflowCount: 0, mUnderflowCount: 0, mAddr: 68:85:A4:6E:F3:36, mCalFailedItemCount: 0
    # BluetoothQualityReportNativeInterface:   }
    # BluetoothQualityReportNativeInterface:   BqrVsLsto: {
    # BluetoothQualityReportNativeInterface:     mConnState: CONN_IDLE(0x00), mBasebandStats: 0x00000000, mSlotsUsed: 0, mCxmDenials: 0, mTxSkipped: 0, mRfLoss: 0, mNativeClock: 0x00000000, mLastTxAckTimestamp: 0x00000000
    # BluetoothQualityReportNativeInterface:   }
    # BluetoothQualityReportNativeInterface: }
    if "mNoRxCount" in msg:
        result = re.search(r"mNoRxCount: \d+, mNakCount: \d+, ", msg)
        # //norx 是没收到回复 nak 是手表收到了 但手表段解析不出来
        return Log(
            translated=f' xxxxxxxxxxxxxxxx 手机没收到设备的心跳包回复，导致连接超时断开({result.group()}) norx值比较大就有问题 xxxxxxxxxxxxxxxx ')
    return None


if __name__ == '__main__':
    result = re.search("device: (.*?),", "connect() - device: 34:47:9A:31:52:CF, auto: false, eattSupport: false")
    print(result.group(1))
    result = re.search("(?<=:).*?(?= )", "dBond State Change Intent:E4:40:97:3C:EB:1C BOND_B")
    # result = re.search("(?<=by: ).*", "disable(): called by: com.android.systemui")
    # result = re.search("(?<=\*).*", "onReCreateBond: 24:*:35:06")
    print(result.group())
    scn_ = "bta_jv_rfcomm_connect: sec_id=0 is zero or BTM_SetSecurityLevel failed, remote_scn:5"
    print(re.search("remote_scn:(\d+)", scn_).group(1))
    # (?<=A).+?(?=B) 匹配规则A和B之间的元素 不包括A和B
