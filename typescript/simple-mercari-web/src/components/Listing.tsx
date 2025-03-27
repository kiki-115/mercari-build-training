import { useState } from 'react';
import { postItem } from '~/api';

interface Prop {
  onListingCompleted: () => void;
}

type FormDataType = {
  name: string;
  category: string;
  image?: string | File;
};

export const Listing = ({ onListingCompleted }: Prop) => {
  const initialState = {
    name: '',
    category: '',
    image: '',
  };
  const [values, setValues] = useState<FormDataType>(initialState);

  const onValueChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setValues({
      ...values,
      [event.target.name]: event.target.value,
    });
  };
  const onFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setValues({
      ...values,
      [event.target.name]: event.target.files ? event.target.files[0] : '', // 画像がない場合は空文字をセット
    });
  };
  const onSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    // 画像がない場合は undefined にする（サーバー側で処理される前提）
    const imageToSend = values.image === '' ? undefined : values.image;

    postItem({
      name: values.name,
      category: values.category,
      image: imageToSend, // image が undefined の場合も送信される
    })
      .catch((error) => {
        console.error('POST error:', error);
        alert('Failed to list this item');
      })
      .finally(() => {
        onListingCompleted();
        setValues(initialState);
      });
  };
  return (
    <div className="Listing">
      <form onSubmit={onSubmit}>
        <div>
          <input
            type="text"
            name="name"
            id="name"
            placeholder="name"
            onChange={onValueChange}
            required
          />
          <input
            type="text"
            name="category"
            id="category"
            placeholder="category"
            onChange={onValueChange}
          />
          <input
            type="file"
            name="image"
            id="image"
            onChange={onFileChange}
          />
          <button type="submit">List this item</button>
        </div>
      </form>
    </div>
  );
};
