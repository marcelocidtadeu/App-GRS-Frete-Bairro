import { useState, useEffect } from "react";
import axios from "axios";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";
import { FileSpreadsheet, MapPin, Loader2 } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const HistoryTable = ({ refreshTrigger }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, [refreshTrigger]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/history`);
      setHistory(response.data.history || []);
    } catch (error) {
      console.error("Erro ao carregar histórico:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "concluido":
        return <Badge className="bg-emerald-100 text-emerald-700 border-emerald-200">Concluído</Badge>;
      case "processando":
        return <Badge className="bg-blue-100 text-blue-700 border-blue-200">Processando</Badge>;
      case "erro":
        return <Badge className="bg-rose-100 text-rose-700 border-rose-200">Erro</Badge>;
      default:
        return <Badge className="bg-slate-100 text-slate-700 border-slate-200">{status}</Badge>;
    }
  };

  const getTipoIcon = (tipo) => {
    return tipo === "cotacao" ? (
      <FileSpreadsheet className="h-4 w-4 text-blue-600" />
    ) : (
      <MapPin className="h-4 w-4 text-emerald-600" />
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        <p>Nenhum processamento realizado ainda.</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-200 overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-slate-50">
            <TableHead className="font-semibold">Tipo</TableHead>
            <TableHead className="font-semibold">Arquivo</TableHead>
            <TableHead className="font-semibold">Status</TableHead>
            <TableHead className="font-semibold">Linhas</TableHead>
            <TableHead className="font-semibold">Erros</TableHead>
            <TableHead className="font-semibold">Data</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {history.map((item) => (
            <TableRow key={item.id} className="hover:bg-slate-50 transition-colors">
              <TableCell>
                <div className="flex items-center gap-2">
                  {getTipoIcon(item.tipo)}
                  <span className="capitalize font-medium">{item.tipo === "cotacao" ? "Cotação" : "CEP"}</span>
                </div>
              </TableCell>
              <TableCell className="font-mono text-sm">{item.arquivo_entrada}</TableCell>
              <TableCell>{getStatusBadge(item.status)}</TableCell>
              <TableCell>{item.linhas_processadas} / {item.total_linhas}</TableCell>
              <TableCell>
                {item.linhas_com_erro > 0 ? (
                  <span className="text-rose-600 font-medium">{item.linhas_com_erro}</span>
                ) : (
                  <span className="text-slate-500">0</span>
                )}
              </TableCell>
              <TableCell className="text-sm text-slate-600">
                {format(new Date(item.created_at), "dd/MM/yyyy HH:mm")}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default HistoryTable;