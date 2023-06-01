<?php 
//try {
//if (!isset(@=chkIssue) or @=chkIssue == array(0)) {
	$client = new SoapClient('http://dc7-web.marsavco.com:8124/soap-wsdl/syracuse/collaboration/syracuse/CAdxWebServiceXmlCC?wsdl',
							 array(
			'login' => 'kossivi',
			'password' => 'A2ggrb012345-'
		)
							);
	$CContext["codeLang"] = "ENG";
	$CContext["poolAlias"] = "LIVE";
	$CContext["requestConfig"] = "adxwss.trace.on=on&adxwss.trace.size=16384&adonix.trace.on=on&adonix.trace.level=3&adonix.trace.size=8";

	// XML string to be passed to the web service
$xmlInput='<PARAM><FLD NAME="BPCORD" >DL000001</FLD>
            <FLD NAME="CUSORDREF" >TEST</FLD>
            <FLD NAME="STOFCY" >M0001</FLD>
            <FLD NAME="BPAADD" >R01A</FLD>
            <TAB ID="SOH4_1" SIZE="1" >
                <LIN NUM="1" >
                    <FLD NAME="ITMREF" >FGSL0009</FLD>
                    <FLD NAME="QTY" >1</FLD>
                    <FLD NAME="DSTOFCY" >M0001</FLD>
                </LIN>
            </TAB>
        </PARAM>';


//$xml=simplexml_load_string($xmlInput);
	
	// Run the subprogram using the SoapClient variable and Calling Context defined earlier
	$data = $client->save($CContext,"ZSOH",$xmlInput);
	$result = $data->resultXml;
	//$xmlInput2 = simplexml_load_string($result);
	//$code = $xmlInput2->xpath('//GRP[@ID="BIS0_1"]/FLD[@NAME="NUM"]');
	//@#txtInvoiceRef = strval($code[0]);
	
	//@#textareaVar001 = $xml;
//}
	print_r($client);
    echo $result;
//}
//catch (Exception $e) {  
//    echo $e;  
//}  

?>
