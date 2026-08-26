function usageNumbers(usage={}){
  const input=Number(usage.input_tokens||0);
  const output=Number(usage.output_tokens||0);
  const cached=Number(usage.input_tokens_details?.cached_tokens||0);
  return {input,output,cached,uncached:Math.max(0,input-cached)};
}


