-- Accepts POST /track/behavior, validates payload, sends to Kafka topic user_behavior_log.
local cjson = require "cjson.safe"
local producer = require "resty.kafka.producer"

ngx.req.read_body()
local raw = ngx.req.get_body_data() or "{}"
local payload = cjson.decode(raw)
if not payload or not payload.userId or not payload.itemId or payload.behaviorType == nil then
    ngx.status = 400
    ngx.say(cjson.encode({ code = 400001, message = "invalid_parameter" }))
    return
end

payload.timestamp = payload.timestamp or (ngx.now() * 1000)
payload.scene = payload.scene or "home"
payload.clientIp = ngx.var.remote_addr
payload.userAgent = ngx.req.get_headers()["User-Agent"] or ""

local broker_list = { { host = "localhost", port = 9092 } }
local p = producer:new(broker_list, { producer_type = "async" })
local ok, err = p:send("user_behavior_log", tostring(payload.userId), cjson.encode(payload))
if not ok then
    ngx.log(ngx.ERR, "kafka send failed: ", err)
    ngx.status = 200  -- never block UX
    ngx.say(cjson.encode({ code = 500301, message = "kafka_error" }))
    return
end

ngx.status = 200
ngx.say(cjson.encode({ code = 0, message = "accepted" }))
