<p align="center">
  <img src="./assets/profile-header.svg" width="100%" alt="Sunnymark7 — Intelligent Systems and Interactive Hardware">
</p>

<p align="center">
  <strong>触觉感知 · 脑机交互 · 嵌入式系统 · 科研工具</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/C%2FC++-00599C?style=flat-square&logo=cplusplus&logoColor=white" alt="C and C++">
  <img src="https://img.shields.io/badge/ESP32-E7352C?style=flat-square&logo=espressif&logoColor=white" alt="ESP32">
  <img src="https://img.shields.io/badge/PyQt-41CD52?style=flat-square&logo=qt&logoColor=white" alt="PyQt">
  <img src="https://img.shields.io/badge/Three.js-000000?style=flat-square&logo=threedotjs&logoColor=white" alt="Three.js">
  <img src="https://img.shields.io/badge/MuJoCo-1A73E8?style=flat-square" alt="MuJoCo">
</p>

## 你好，我是 Vic

我关注软硬件结合的智能交互系统：从传感器采集与嵌入式固件，到桌面端数据处理、三维可视化和实验原型。这里按“项目群”组织仓库，让每个项目的目标、边界和入口一目了然。

> 当前重点：构建结合多通道触觉、手部姿态与实时三维反馈的智能手套系统。

## 项目地图

| 项目群 | 解决什么问题 | 仓库构成 | 状态 |
| --- | --- | --- | --- |
| **eHand 智能触觉手套** | 80 通道压力采集、IMU 姿态、BLE/串口通信与 MuJoCo 三维反馈 | 软件与硬件 2 个私有仓库 | `Active R&D` |
| **脑机交互与手部可视化** | SSVEP 刺激、三维手部模型与 EEG 采集实验 | [SSVEP-3dhand](https://github.com/Sunnymark7/SSVEP-3dhand) + 1 个私有仓库 | `Prototype` |
| **嵌入式开发工具** | ESP32 固件识别、串口检测和一键烧录；高精度 ADC 采集 | [esp_downloadtool](https://github.com/Sunnymark7/esp_downloadtool) + 1 个私有仓库 | `Usable` |
| **科研测量与工程仿真** | 恒温槽标定、车辆悬架动力学等实验工具 | 2 个私有仓库 | `Research` |
| **Web 实验与创意原型** | 轻量网页交互和概念验证 | 2 个私有仓库 | `Sandbox` |

<sub>🔒 私有仓库仅展示项目方向与数量，不公开代码、链接或敏感细节。</sub>

## 精选项目

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>🧠 <a href="https://github.com/Sunnymark7/SSVEP-3dhand">SSVEP-3dhand</a></h3>
      <p>浏览器端 SSVEP 三维手部交互演示。支持左右手镜像、骨骼调试、单指动画以及五频视觉刺激块。</p>
      <p><code>Three.js</code> <code>WebGL</code> <code>JavaScript</code> <code>BCI</code></p>
      <a href="https://github.com/Sunnymark7/SSVEP-3dhand"><strong>查看项目 →</strong></a>
    </td>
    <td width="50%" valign="top">
      <h3>⚡ <a href="https://github.com/Sunnymark7/esp_downloadtool">esp_downloadtool</a></h3>
      <p>面向 ESP32 固件包的一键下载工具。自动识别固件文件、烧录地址和串口，并提供分阶段进度反馈。</p>
      <p><code>Python</code> <code>PyQt</code> <code>esptool</code> <code>ESP32</code></p>
      <a href="https://github.com/Sunnymark7/esp_downloadtool"><strong>查看项目 →</strong></a>
    </td>
  </tr>
</table>

## 我在构建什么

```text
传感器 / EEG  ──>  嵌入式采集  ──>  通信与数据处理  ──>  三维交互与实验应用
```

- **感知层：** 压力阵列、IMU、EEG 与高精度 ADC
- **设备层：** ESP32-S3、实时采样、BLE / Serial 协议
- **应用层：** Python 桌面工具、实时可视化、标定与数据分析
- **交互层：** Three.js / MuJoCo 手部模型、BCI 与触觉反馈实验

## 仓库组织约定

| 标记 | 含义 |
| --- | --- |
| `project-ehand` | eHand 软件、固件、电子与结构设计 |
| `project-neurotech` | SSVEP、EEG 与神经交互实验 |
| `project-embedded` | 嵌入式采集、烧录与硬件工具 |
| `project-instrumentation` | 标定、测量与科研仪器软件 |
| `project-simulation` | 动力学、模型与工程仿真 |
| `project-experiments` | 独立网页实验与概念原型 |

## 技术方向

`Python` · `C / C++` · `C#` · `ESP32-S3` · `BLE` · `Serial` · `PyQt` · `MuJoCo` · `Three.js` · `WebGL`

---

<p align="center">
  <i>把传感器数据变成可以理解、可以交互的系统。</i><br>
  <a href="https://github.com/Sunnymark7?tab=repositories">浏览全部公开仓库</a>
</p>
