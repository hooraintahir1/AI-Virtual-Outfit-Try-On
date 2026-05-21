
export class Outfit {
  
  constructor(data) {
    this.id = data.id;
    this.name = data.name;
    this.file = data.file;
    this.url = data.url ?? `/outfits/${data.file}`;
  }
}
