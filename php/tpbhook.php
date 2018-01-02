<?php
$signature = $_SERVER["HTTP_X_TPB_SIGNATURE"];
$payload = file_get_contents("php://input");
$secret = getenv("tpbtowootsecret");
$computed_sig = hash_hmac("sha1", $payload, $secret);
if ($computed_sig != $signature)
{
    echo "Signature does not match";
    die;
}
$data = json_decode($payload);
$message = $data->message;
$recipient = $data->recipient;

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, "https://localhost:16000/1");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 0);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(array("to" => "tpb", "tpbrecipient" => $recipient, "message" => $message)));
curl_setopt($ch, CURLOPT_POST, 1);
$result = curl_exec($ch);

if (curl_errno($ch)) {
    echo curl_error($ch);
} else {
    curl_close($ch);
}
echo $result;

