function flattenCurriculum(curriculum,courses){
  const rows=[];
  for(const course of courses||[]){
    const units=curriculum?.[course]||{};
    for(const [unit,topics] of Object.entries(units)){
      for(const topic of topics||[]) rows.push({course,unit,topic});
    }
  }
  return rows;
}


