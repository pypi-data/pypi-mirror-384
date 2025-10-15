import { app } from "../../scripts/app.js";
import '../BizyAir/bizyair_frontend.js'
import { hideWidget } from './tool.js'

// 动态配置缓存
let nodeConfigCache = null;
let configLoadPromise = null;
let storageClearedOnce = false;

// API配置
const CONFIG_API_URL = 'https://bizyair.cn/api/special/comfyagent_node_config?t=' + Math.floor(Date.now() / 60000);

// 获取节点配置的API函数
async function fetchNodeConfig() {
    if (nodeConfigCache) {
        return nodeConfigCache;
    }

    if (configLoadPromise) {
        return configLoadPromise;
    }

    configLoadPromise = (async () => {
        try {
            console.log('正在从API获取节点配置...');
            const response = await fetch(CONFIG_API_URL, { credentials: 'include' });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.code === 20000 && result.data && result.data.weight_load_nodes) {
                nodeConfigCache = result.data.weight_load_nodes;
                console.log('节点配置加载成功:', Object.keys(nodeConfigCache).length, '个节点');
                return nodeConfigCache;
            } else {
                throw new Error('API返回数据格式不正确');
            }
        } catch (error) {
            console.error('获取节点配置失败:', error);
            nodeConfigCache = null;
            return null;
        }
    })();

    return configLoadPromise;
}

// 启动时后台预取（不阻塞后续逻辑）
try { void fetchNodeConfig(); } catch (e) { /* noop */ }

const HAZY_WHITELIST_NODES = {

}

const possibleWidgetNames=[
    "clip_name",
    "clip_name1",
    "clip_name2",
    "clip_name3",
    "clip_name4",
    "ckpt_name",
    "lora_name",
    "name",
    "lora",
    "lora_01",
    "lora_02",
    "lora_03",
    "lora_04",
    "lora_1_name",
    "lora_2_name",
    "lora_3_name",
    "lora_4_name",
    "lora_5_name",
    "lora_6_name",
    "lora_7_name",
    "lora_8_name",
    "lora_9_name",
    "lora_10_name",
    "lora_11_name",
    "lora_12_name",
    "model_name",
    "control_net_name",
    "ipadapter_file",
    "unet_name",
    "vae_name",
    "model",
    "model_name",
    "instantid_file",
    "pulid_file",
    "style_model_name",
    "yolo_model",
    "face_model",
    "bbox_model_name",
    "sam_model_name",
    "model_path",
    "upscale_model",
    "supir_model",
    "sdxl_model",
    "upscale_model_1",
    "upscale_model_2",
    "upscale_model_3",
    "sam_model",
    "sam2_model",
    "grounding_dino_model"
]

// 读取 mode_type（不再兼容旧的 modelType）
function getModelTypeFromInput(inputConfig) {
    console.log('inputConfig', inputConfig);
    if (!inputConfig) return undefined;
    console.log('inputConfig', inputConfig);
    return inputConfig.mode_type;
}

// 根据节点名称获取节点配置信息（名单优先，正则补充；不阻塞返回）
async function getNodeConfig(nodeName) {
    if (/bizyair/i.test(nodeName)) {
        return null;
    }

    // 1) 名单（API）优先（仅用缓存，不等待网络）
    if (nodeConfigCache && nodeConfigCache[nodeName]) {
        return { nodeName, config: nodeConfigCache[nodeName] };
    }

    // 若尚未发起请求，后台发起一次
    if (!configLoadPromise) { try { void fetchNodeConfig(); } catch (e) {} }

    // 2) 正则补充：如 XxxLoader => Xxx（立即返回，不等待API）
    const regex = /^(\w+).*Loader.*/i;
    const match = nodeName.match(regex);
    if (match) {
        const inferredType = match[1];
        return { nodeName, config: { inputs: { [nodeName]: { mode_type: inferredType, required: true } } } };
    }
    return null;
}

function createSetWidgetCallback(nodeConfig, selectedBaseModels = []) {
    return function setWidgetCallback() {
        if (!nodeConfig || !nodeConfig.config || !nodeConfig.config.inputs) {
            console.warn('节点配置无效:', nodeConfig);
            return;
        }

        const inputs = nodeConfig.config.inputs;
        const inputKeys = Object.keys(inputs);

        // 根据API配置找到对应的widget
        const targetWidgets = [];
        inputKeys.forEach(inputKey => {
            const widget = this.widgets.find(w => w.name === inputKey);
            if (widget) {
                targetWidgets.push({
                    widget: widget,
                    inputKey: inputKey,
                    inputConfig: inputs[inputKey]
                });
            }
        });

        // 如果没有找到匹配的widget，使用原来的逻辑作为备选
        if (targetWidgets.length === 0) {
            const fallbackWidgets = this.widgets.filter(widget => possibleWidgetNames.includes(widget.name));
            fallbackWidgets.forEach((wdt, index) => {
                const firstInput = Object.values(inputs)[0];
                if (firstInput) {
                    targetWidgets.push({
                        widget: wdt,
                        inputKey: wdt.name,
                        inputConfig: firstInput,
                        index: index
                    });
                }
            });
        }

        targetWidgets.forEach(({ widget, inputKey, inputConfig, index }) => {
            // 检查是否禁用comfyagent
            if (inputConfig.disable_comfyagent) {
                console.log(`跳过禁用的widget: ${inputKey}`);
                return;
            }

            widget.value = widget.value || "to choose";
            widget.mouse = function(e, pos, canvas) {
                try {
                    if (e.type === "pointerdown" || e.type === "mousedown" || e.type === "click" || e.type === "pointerup") {
                        e.preventDefault();
                        e.stopPropagation();
                        e.widgetClick = true;
                        window.parent.postMessage({
                            type: 'collapsePublishWorkflowDialog',
                            method: 'collapsePublishWorkflowDialog',
                            result: true
                        }, '*');
                        const currentNode = this.node;

                        if (!currentNode || !currentNode.widgets) {
                            console.warn("Node or widgets not available");
                            return false;
                        }

                        if (typeof bizyAirLib !== 'undefined' && typeof bizyAirLib.showModelSelect === 'function') {
                            bizyAirLib.showModelSelect({
                                modelType: [getModelTypeFromInput(inputConfig)],
                                selectedBaseModels,
                                onApply: (version, model) => {
                                    if (!currentNode || !currentNode.widgets) return;

                                    // 更新widget值
                                    widget.value = version.file_name;

                                    // 找到对应的隐藏字段（固定命名：model_version_id, model_version_id2...）
                                    let modelVersionField;
                                    // 真实绑定顺序应与targetWidgets相同，因此通过当前widget在targetWidgets的索引定位
                                    const twIndex = targetWidgets.findIndex(tw => tw.widget === widget);
                                    const fieldName = twIndex === 0 ? "model_version_id" : `model_version_id${twIndex + 1}`;
                                    modelVersionField = currentNode.widgets.find(w => w.name === fieldName);

                                    if (model && modelVersionField && version) {
                                        modelVersionField.value = version.id;
                                        currentNode.setDirtyCanvas(true);

                                    // 删除节点上的感叹号徽章
                                    if (currentNode && currentNode.badges && Array.isArray(currentNode.badges)) {
                                        // 移除 text 为 '!' 的徽章
                                        currentNode.badges = currentNode.badges.filter(badgeFn => {
                                            try {
                                                const badge = typeof badgeFn === 'function' ? badgeFn() : badgeFn;
                                                return badge.text !== '!';
                                            } catch (e) {
                                                return true;
                                            }
                                        });
                                        // 同时移除 hasTips 标记
                                        if (currentNode.hasTips) {
                                            delete currentNode.hasTips;
                                        }
                                    }
                                    }
                                }
                            });
                        } else {
                            console.error("bizyAirLib not available");
                        }
                        return false;
                    }
                } catch (error) {
                    console.error("Error handling mouse event:", error);
                }
            };

            widget.options = widget.options || {};
            widget.options.values = () => [];
            widget.options.editable = false;
            widget.clickable = true;
            widget.processMouse = true;
        });
    }
}

function setupNodeMouseBehavior(node, nodeConfig) {
    // 固定隐藏主版本ID字段（其余编号字段为hidden类型本身不可见）
    hideWidget(node, "model_version_id");

    // 只设置必要的状态信息，不修改onMouseDown（已在上面的扩展中处理）
    if (!node._bizyairState) {
        node._bizyairState = {
            lastClickTime: 0,
            DEBOUNCE_DELAY: 300,
            nodeConfig: nodeConfig
        };
    }
}
function addBadge(node) {
    const customBadge = new LGraphBadge({
        text: '!',
        fgColor: 'white',
        bgColor: '#FF6B6B',
        fontSize: 12,
        padding: 8,
        height: 20,
        cornerRadius: 10
      })
    if (!Array.isArray(node.badges)) {
        node.badges = []
    }
    if (node.hasTips) {
        return
    }
    node.badges.push(() => customBadge);
    node.hasTips = true;
}
app.registerExtension({
    name: "bizyair.hook.load.model",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {

        if (!storageClearedOnce) {
            // localStorage.removeItem('workflow')
            localStorage.clear()
            sessionStorage.clear()
            storageClearedOnce = true;
        }
        const interval = setInterval(() => {
            if (window.switchLanguage) {
                window.switchLanguage('zh')
                clearInterval(interval)
            }
        }, 100)

        // 异步获取节点配置
        const nodeConfig = await getNodeConfig(nodeData.name);
        if (nodeConfig) {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                try {
                    const inputs = nodeConfig.config.inputs;
                    const inputKeys = Object.keys(inputs);

                    // 计算需处理的目标widgets（按禁用过滤后再确定数量和索引）
                    let targetWidgets = [];
                    // 优先按API字段名匹配
                    inputKeys.forEach((key) => {
                        const cfg = inputs[key];
                        if (cfg && !cfg.disable_comfyagent) {
                            const w = this.widgets.find(x => x.name === key);
                            if (w) targetWidgets.push(w);
                        }
                    });
                    // 如果一个都没匹配到，使用fallback列表
                    if (targetWidgets.length === 0) {
                        const fallback = this.widgets.filter(w => possibleWidgetNames.includes(w.name));
                        // fallback 不再过滤 disable 标记，因为此路径说明API key未命中
                        targetWidgets = fallback;
                    }

                    // 按目标widgets数量创建隐藏字段（model_version_id, model_version_id2...）
                    targetWidgets.forEach((_, idx) => {
                        const fieldName = idx === 0 ? "model_version_id" : `model_version_id${idx + 1}`;
                        let mv = this.widgets.find(w => w.name === fieldName);
                        if (!mv) {
                            mv = this.addWidget("hidden", fieldName, "", function(){}, { serialize: true, values: [] });
                        }
                    });

                    // 如果没有找到匹配的输入字段，使用兼容性逻辑
                    if (inputKeys.length === 0) {
                        const targetWidget = this.widgets.filter(widget => possibleWidgetNames.includes(widget.name));
                        targetWidget.forEach((widget, index) => {
                            let model_version_id;
                            if (index === 0) {
                                model_version_id = this.widgets.find(w => w.name === "model_version_id");
                                if (!model_version_id) {
                                    model_version_id = this.addWidget("hidden", "model_version_id", "", function(){
                                    }, {
                                        serialize: true,
                                        values: []
                                    });
                                }
                            } else {
                                const fieldName = `model_version_id${index + 1}`;
                                model_version_id = this.widgets.find(w => w.name === fieldName);
                                if (!model_version_id) {
                                    model_version_id = this.addWidget("hidden", fieldName, "", function(){
                                    }, {
                                        serialize: true,
                                        values: []
                                    });
                                }
                            }
                        });
                    }

                    const result = onNodeCreated?.apply(this, arguments);
                    let selectedBaseModels = [];

                    // 检查是否需要添加徽章（与targetWidgets一致的索引规则）
                    targetWidgets.forEach((widget, idx) => {
                        const fieldName = idx === 0 ? "model_version_id" : `model_version_id${idx + 1}`;
                        const mv = this.widgets.find(w => w.name === fieldName);
                        if (mv) {
                            setTimeout(() => {
                                if (widget.value != 'NONE' && !mv.value) addBadge(this);
                            }, 200);
                        }
                    });

                    // 如果没有找到匹配的输入字段，使用兼容性逻辑检查徽章
                    if (inputKeys.length === 0) {
                        const targetWidget = this.widgets.filter(widget => possibleWidgetNames.includes(widget.name));
                        targetWidget.forEach((widget, index) => {
                            let model_version_id;
                            if (index === 0) {
                                model_version_id = this.widgets.find(w => w.name === "model_version_id");
                            } else {
                                const fieldName = `model_version_id${index + 1}`;
                                model_version_id = this.widgets.find(w => w.name === fieldName);
                            }

                            if (model_version_id) {
                                setTimeout(() => {
                                    if (widget.value != 'NONE' && !model_version_id.value) {
                                        addBadge(this);
                                    }
                                }, 200);
                            }
                        });
                    }

                    createSetWidgetCallback(nodeConfig, selectedBaseModels).call(this);
                    return result;
                } catch (error) {
                    console.error("Error in node creation:", error);
                }
            };
        }
    },
    async nodeCreated(node) {
        const nodeConfig = await getNodeConfig(node?.comfyClass);

        if (nodeConfig) {
            setupNodeMouseBehavior(node, nodeConfig);
        }
    }
})
