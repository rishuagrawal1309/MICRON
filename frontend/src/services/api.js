import axios from "axios";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000",
});

export const getBomTree = async (material) => {
    const response = await API.get(`/api/bom/${material}/tree`);
    return response.data;
};

export default API;